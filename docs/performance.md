# Performance Guide

## Architecture Performance Characteristics

### Async I/O
The entire backend is fully async (FastAPI + asyncpg + aiosqlite + Redis async). The event loop is never blocked by I/O operations.

### Connection Pooling

| Resource | Pool Size | Overflow | Notes |
|----------|-----------|----------|-------|
| PostgreSQL | 20 (per worker) | 10 | `pool_pre_ping=True` detects stale connections |
| Redis | 50 connections | — | Shared across all coroutines |

For 4 Uvicorn workers: 4 × 20 = 80 max PostgreSQL connections.
Set `max_connections` in `postgresql.conf` to at least 100.

### Caching Strategy

| Data | Cache Key | TTL | Notes |
|------|-----------|-----|-------|
| Dashboard stats | `dashboard:{user_id}` | 15s | Also pushed via WebSocket |
| Analytics summary | `analytics:summary` | 5min | Expensive aggregate queries |
| Call volume | `analytics:volume:{days}` | 5min | |
| Health check | `health:ready` | 10s | Avoids DB ping on every /health/ready |
| Billing context | `billing:context:{case_id}` | 60s | Agent tool calls |

---

## Database Indexes

All hot-path query columns are indexed (see `docs/database.md`).

Key indexes:
- `billing_cases.status` — filter by status (most common query)
- `call_jobs.status` — queue management
- `call_sessions.twilio_call_sid` — webhook lookup (unique)
- `users.email` — login (unique)
- `refresh_tokens.token_hash` — auth refresh (unique)
- `audit_logs.actor_id, action, resource_type` — audit search

---

## Query Optimization

### Pagination
All list endpoints use `OFFSET/LIMIT`. For very large tables (> 1M rows), consider cursor-based pagination.

### N+1 Prevention
Use `selectinload()` for relationships:
```python
# Good
stmt = select(BillingCase).options(selectinload(BillingCase.call_jobs))

# Bad — N+1: loads each call_job separately
cases = await repo.list()
for case in cases:
    jobs = case.call_jobs  # lazy load — N queries
```

### Aggregate Queries
Analytics uses direct SQL aggregates (GROUP BY) rather than loading all rows:
```python
result = await db.execute(
    select(
        func.date(CallSession.created_at).label("date"),
        func.count().label("total"),
    ).group_by(func.date(CallSession.created_at))
)
```

---

## Frontend Performance

### Code Splitting
All page components are lazy-loaded (`React.lazy` + `Suspense`). Initial bundle only loads auth pages + layout.

### Query Caching
TanStack Query caches all API responses:
- `staleTime: 30_000` (global default)
- Dashboard stats: refetch every 15s (also updated by WebSocket)
- Active calls: refetch every 10s
- Analytics: `staleTime: 60_000` (rarely changes)

### React.memo
`CaseRow` in BillingCases is memoized to prevent re-renders when unrelated state changes.

---

## Load Testing Estimates

### Single Instance Capacity (4 Uvicorn workers, 4 CPUs, 8GB RAM)

| Metric | Estimate | Notes |
|--------|----------|-------|
| HTTP requests | ~500 req/s | Read-heavy workload |
| Concurrent WebSockets | ~200 | Dashboard connections |
| Concurrent calls | ~20-50 | Limited by Twilio + ElevenLabs |
| DB connections | 80 max | 4 workers × 20 pool |

### Bottlenecks at Scale

1. **Active call handling** — Each call opens a Twilio Media Stream WebSocket + ElevenLabs WebSocket. Concurrency is limited by available threads and external API rate limits.

2. **LLM latency** — OpenAI API latency is the dominant factor in turn latency. Use GPT-4o-mini for lower latency at some accuracy trade-off.

3. **Database at 1000+ users** — Add a read replica for analytics queries. Partition `call_sessions` and `transcripts` by month for large deployments.

4. **WebSocket connections** — The dashboard WebSocket is broadcast-based. At 1000+ concurrent users, consider Redis Pub/Sub for cross-worker message distribution.

---

## Tuning for 1000+ Concurrent Users

```bash
# Increase Uvicorn workers (in Dockerfile CMD)
# Rule: workers = (2 × CPUs) + 1
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000",
     "--workers", "9",   # 4 CPUs → 9 workers
     "--no-access-log"]

# Increase PostgreSQL pool per worker
DB_POOL_SIZE=15   # 9 workers × 15 = 135 connections
# Set max_connections=200 in postgresql.conf

# Increase Redis connections
REDIS_MAX_CONNECTIONS=100

# Add PostgreSQL connection pooler (PgBouncer) for 5000+ users
```

---

## Performance Monitoring

Key Prometheus metrics to watch:

```
# P95 request latency > 2s → investigate
histogram_quantile(0.95, http_request_duration_seconds)

# Error rate > 1% → alert
rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m])

# LLM latency (turn latency proxy)
histogram_quantile(0.95, llm_response_duration_seconds)

# Active WebSocket connections
active_websocket_connections

# Cache hit rate
rate(redis_cache_hits_total[5m]) / (rate(redis_cache_hits_total[5m]) + rate(redis_cache_misses_total[5m]))
```

---

## Recommended Load Test Scenarios

Use [Locust](https://locust.io) or [k6](https://k6.io):

```
Scenario 1 — Dashboard users (100 concurrent)
  - GET /health/ready: 1 req/5s per user
  - GET /dashboard/stats: 1 req/15s per user
  - WS /ws/dashboard: maintain 1 connection per user

Scenario 2 — Billing operators (50 concurrent)
  - GET /billing-cases: 1 req/10s
  - POST /billing-cases: 1 req/60s
  - POST /call-jobs: 1 req/120s

Scenario 3 — Active call spike (20 concurrent calls)
  - Each call: WS media stream open for 5 min
  - LLM invocations: ~1/15s per call

Target SLOs:
  - P50 HTTP < 100ms
  - P95 HTTP < 500ms
  - P99 HTTP < 2s
  - Error rate < 0.1%
  - WebSocket reconnect < 5s
```
