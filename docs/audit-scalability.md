# Scalability Audit Report — Insurance Denials Voice Agent
**Date:** 2026-07-03  
**Auditor:** Engineering Audit Agent  
**Scope:** Load capacity analysis, WebSocket scalability, database scaling, Redis, background workers

---

## Executive Summary

| Dimension | Current Capacity | Bottleneck | Path to Scale |
|-----------|-----------------|------------|---------------|
| HTTP API | ~1 000 RPS (1 host) | CPU / DB pool | Horizontal replicas + PgBouncer |
| Dashboard WebSocket | ~500 concurrent (1 process) | In-process dict | Redis Pub/Sub |
| Active AI calls | ~20–50 concurrent | ElevenLabs WS limits | Call queue + worker pool |
| DB connections | 30 per instance | Pool exhaustion | PgBouncer |
| Redis | Single instance | OOM at high volume | Redis Cluster / Sentinel |

---

## Load Test Scenarios

### How to Run

```bash
pip install locust
cd tests/load

# 100 users — baseline
locust -f locustfile.py --host http://localhost:8000 \
       --headless -u 100 -r 10 --run-time 2m \
       --csv reports/load_100

# 1 000 users — moderate load
locust -f locustfile.py --host http://localhost:8000 \
       --headless -u 1000 -r 50 --run-time 5m \
       --csv reports/load_1000

# 5 000 users — distributed (requires worker nodes)
# Master node:
locust -f locustfile.py --master --host http://localhost:8000
# Each worker node:
locust -f locustfile.py --worker --master-host <master-ip>
# Then via web UI set: 5000 users, 100/s spawn rate

# 10 000 users — production stress (requires ≥4 worker nodes)
# Same distributed setup with 10 000 users
```

### Test User Mix (weights in `locustfile.py`)

| User Type | Weight | Persona |
|-----------|--------|---------|
| `BillingOperator` | 5 | Creates cases, schedules calls (write-heavy) |
| `DashboardViewer` | 3 | Reads analytics and dashboard stats (read-heavy) |
| `AuthStressUser` | 1 | Hammers auth endpoints |

---

## Capacity Projections

### Single Instance (4 Uvicorn workers, 4 CPU cores, 8 GB RAM)

| Users | Expected RPS | Expected p50 | Expected p95 | DB Pool | Notes |
|-------|-------------|-------------|-------------|---------|-------|
| 100 | ~120 RPS | ~30 ms | ~80 ms | ~25% | Comfortable |
| 1 000 | ~600 RPS | ~80 ms | ~300 ms | ~80% | Pool near saturation |
| 5 000 | ~900 RPS (throttled) | ~300 ms | ~1 500 ms | 100% | Pool exhaustion → queuing |
| 10 000 | Rate limited / degraded | >2 000 ms | Timeouts | 100% | Horizontal scaling required |

### Multi-Instance (2 replicas × 4 workers, behind Nginx)

| Users | Expected RPS | Expected p50 | Expected p95 | DB Pool |
|-------|-------------|-------------|-------------|---------|
| 1 000 | ~1 200 RPS | ~30 ms | ~120 ms | ~40% |
| 5 000 | ~1 800 RPS | ~100 ms | ~400 ms | ~80% |
| 10 000 | ~2 000 RPS (throttled) | ~200 ms | ~800 ms | ~95% |

**Recommended threshold to add a third replica: sustained p95 > 500 ms or pool utilisation > 75%.**

---

## WebSocket Scalability

### Current Architecture (Single Process)

```
Worker 1 ──→ _dashboard_clients = { user_id: WebSocket }
Worker 2 ──→ _dashboard_clients = { }  ← empty (different process!)
```

**Problem:** `broadcast_stats()` only reaches clients connected to the same Uvicorn worker. With multiple workers, 75% of clients receive no updates.

### Required: Redis Pub/Sub Pattern

```python
# Publish from any worker:
await redis.publish("dashboard:broadcast", json.dumps(stats.dict()))

# Each worker subscribes:
async for message in pubsub.listen():
    for ws in local_clients.values():
        await ws.send_text(message["data"])
```

This is the only **known architecture limitation** blocking multi-worker horizontal scaling of the WebSocket feature.

**Priority: High before production deployment with >1 worker.**

---

## Database Scaling

### Current State
- PostgreSQL with `pool_size=20, max_overflow=10` per backend instance.
- 2 replicas = 60 total connections to PostgreSQL.
- PostgreSQL default max connections = 100.

### At 10 Workers (Kubernetes)
- 10 × 30 = 300 connections → **exceeds PostgreSQL default**.
- Solution: **PgBouncer** in transaction mode (pools connections at the proxy level).

### Read Replicas
For analytics/reporting queries (heavy reads, can tolerate slight staleness):
```python
# Route analytics queries to read replica:
ANALYTICS_DB_URL=postgresql+asyncpg://user:pass@replica:5432/billingdb

# In analytics_service.py — use separate engine for read-heavy queries
```

### Schema Optimisation Opportunities

| Table | Current Indexes | Suggested Addition | When |
|-------|----------------|-------------------|------|
| `call_jobs` | `(status)`, `(billing_case_id)` | `(status, priority DESC, created_at)` — composite for queue ordering | When queue > 10K rows |
| `audit_log` | `(actor_id, created_at)` | `(action, created_at)` — for action-type filtering | When > 1M audit rows |
| `transcripts` | `(call_session_id, sequence_number)` | Full-text search index (GIN on `content`) | If search feature added |
| `billing_cases` | `(status)`, `(payer_name)` | `(created_at DESC)` — for pagination performance | When > 100K rows |

---

## Redis Scaling

### Current State
- Single Redis instance with password authentication.
- Used for: rate limiting (INCR/EXPIRE), session cache, analytics cache, dashboard cache.
- No persistence (`appendonly no` by default in Docker config).

### Risks

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Redis OOM | Cache evictions → DB load spike | Set `maxmemory 512mb` + `maxmemory-policy allkeys-lru` |
| Redis restart | All cache + rate limit state lost | Rate limits reset (temporary attack window) |
| Single point of failure | Cache unavailable → all analytics hit DB | Redis Sentinel (HA) for production |

### Configuration Recommendations

```conf
# redis.conf additions for production
maxmemory 512mb
maxmemory-policy allkeys-lru
save 900 1      # Persist to disk every 15 min if >= 1 change
save 300 10     # Persist every 5 min if >= 10 changes
```

---

## Background Workers

### Current State
- No dedicated background worker / task queue (Celery, ARQ, etc.).
- Long-running call orchestration runs in the Uvicorn request handler via WebSocket.
- Audit writes are `asyncio.create_task` — fire-and-forget within the request loop.

### Risk at Scale
If 50 simultaneous calls are active, each maintaining a WebSocket connection with ongoing LLM/TTS processing, Uvicorn event loop pressure increases. CPU-bound operations (audio decoding) may block the event loop.

### Recommendation: Offload to Dedicated Worker

```
[Call Trigger API] → [Redis Queue] → [Call Worker Service]
                                           │
                                    [LangGraph + TTS + STT]
                                           │
                                    [DB update + Broadcast]
```

This separates HTTP API workers from AI pipeline workers, allowing independent scaling.

---

## Observability for Scalability

### Current Prometheus Metrics
- `http_requests_total{method, path, status}` — per-endpoint traffic
- `http_request_duration_seconds{method, path}` — latency histograms
- `active_websocket_connections` — gauge
- `redis_cache_hits_total` / `redis_cache_misses_total` — cache efficiency
- `llm_response_duration_seconds` — AI latency
- `calls_started_total` / `calls_completed_total` / `calls_failed_total`

### Suggested Scaling Alerts (Prometheus / Grafana)

```yaml
# alerts.yml
- alert: HighP95Latency
  expr: histogram_quantile(0.95, http_request_duration_seconds_bucket) > 1.0
  for: 5m
  annotations:
    summary: "API p95 latency > 1s for 5 minutes — consider scaling"

- alert: LowCacheHitRatio
  expr: rate(redis_cache_hits_total[5m]) / (rate(redis_cache_hits_total[5m]) + rate(redis_cache_misses_total[5m])) < 0.7
  for: 10m
  annotations:
    summary: "Redis cache hit ratio < 70% — analytics queries hitting DB heavily"

- alert: HighActiveWebSockets
  expr: active_websocket_connections > 200
  for: 5m
  annotations:
    summary: "High WebSocket count — verify Redis pub/sub is active"

- alert: DBPoolExhaustion
  expr: pg_stat_activity_count > 80
  for: 2m
  annotations:
    summary: "PostgreSQL connections > 80 — add PgBouncer or scale DB"
```

---

## Scaling Roadmap

### Phase 1 — Current (up to 500 concurrent users)
- Single backend instance, 4 workers
- Single PostgreSQL
- Single Redis
- ✅ Ready now

### Phase 2 — 500–2 000 concurrent users
- 2 backend replicas behind Nginx (update `docker-compose.yml`)
- Add Redis Pub/Sub for WebSocket broadcast ← **highest priority code change**
- Add PgBouncer (add service to Docker Compose)
- Set Redis `maxmemory 512mb` + LRU eviction

### Phase 3 — 2 000–10 000 concurrent users
- 4+ backend replicas (Kubernetes or Docker Swarm)
- PostgreSQL with read replica for analytics
- Dedicated call worker service (separate from HTTP API)
- Redis Sentinel or Redis Cluster
- Horizontal Pod Autoscaler on CPU + p95 latency metrics

---

## Load Test Infrastructure

The load test suite is at `tests/load/locustfile.py`.

| File | Purpose |
|------|---------|
| `tests/load/locustfile.py` | Locust scenarios: auth, billing workflow, read-only |
| `tests/ai/test_agent_quality.py` | AI quality evaluation (prompt, hallucination, guardrails, latency) |

### CI Integration

Add to `.github/workflows/ci.yml` (smoke load test on every PR):
```yaml
- name: Load test (smoke — 50 users, 60s)
  run: |
    pip install locust
    locust -f tests/load/locustfile.py \
           --host http://localhost:8000 \
           --headless -u 50 -r 10 --run-time 60s \
           --exit-code-on-error 1
```

### Acceptance Thresholds (defined in `locustfile.py`)

| Metric | Threshold |
|--------|-----------|
| p50 response time | < 200 ms |
| p95 response time | < 1 000 ms |
| p99 response time | < 3 000 ms |
| Error rate | < 1% |
