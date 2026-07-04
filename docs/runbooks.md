# Runbooks

## 1. Deployment Runbook

### Standard Deployment

```bash
# Pre-deployment checklist
- [ ] All tests pass on CI
- [ ] Migration tested on staging
- [ ] .env values confirmed
- [ ] Backup taken (see backup runbook)

# Steps
cd /opt/billing-agent
git pull origin main
docker compose build
docker compose up -d
docker compose exec backend alembic upgrade head

# Verify
curl https://your-domain.com/health/ready
docker compose ps   # all containers "Up (healthy)"
```

---

## 2. Rollback Runbook

### Code Rollback

```bash
cd /opt/billing-agent
git log --oneline -10   # find previous working commit
git checkout <commit-hash>
docker compose build
docker compose up -d
```

### Database Rollback

```bash
# Check current revision
docker compose exec backend alembic current

# Downgrade one step
docker compose exec backend alembic downgrade -1

# Downgrade to specific revision
docker compose exec backend alembic downgrade <revision_id>
```

**Warning:** Rollback only if absolutely necessary. Test `downgrade()` in staging first.

---

## 3. Incident Response Runbook

### P1 — Service Down (5xx errors or no response)

```bash
# 1. Check service health
curl https://your-domain.com/health/ready

# 2. Check container status
docker compose ps

# 3. Check logs (last 100 lines)
docker compose logs --tail=100 backend

# 4. Check resources
docker stats --no-stream

# 5. If container crashed — restart
docker compose restart backend

# 6. If DB connection issue — check postgres
docker compose exec postgres pg_isready -U agent
docker compose logs postgres --tail=50

# 7. If Redis issue
docker compose exec redis redis-cli -a $REDIS_PASSWORD ping
docker compose logs redis --tail=50

# 8. Escalation: If not resolved in 15 minutes → rollback
```

### P2 — Slow Responses

```bash
# Check metrics
curl http://localhost:8000/metrics | grep http_request_duration

# Check DB query times
docker compose exec postgres psql -U agent billing_agent -c \
  "SELECT query, mean_exec_time, calls FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 10;"

# Check Redis memory
docker compose exec redis redis-cli -a $REDIS_PASSWORD info memory

# Check system resources
docker stats --no-stream
```

### P3 — AI Agent Errors

```bash
# Check for LLM errors
docker compose logs backend | grep "openai\|LLM\|langgraph" | tail -50

# Check ElevenLabs connectivity
docker compose logs backend | grep "elevenlabs\|STT\|TTS" | tail -50

# Check Twilio webhook delivery
# Log in to Twilio Console → Debugger → Errors
```

---

## 4. Disaster Recovery Runbook

### Full Server Loss

```bash
# 1. Provision new server
# 2. Install Docker
sudo apt update && sudo apt install -y docker.io docker-compose-v2
# 3. Clone repo
git clone https://github.com/your-org/billing-voice-agent.git /opt/billing-agent
# 4. Restore .env from secure vault
# 5. Start infrastructure
cd /opt/billing-agent
docker compose up -d postgres redis
# 6. Restore DB from backup
docker compose exec -T postgres psql -U agent billing_agent < /path/to/backup.sql
# 7. Start application
docker compose up -d
docker compose exec backend alembic upgrade head
# 8. Verify
curl https://your-domain.com/health/ready
# 9. Update DNS if IP changed
# 10. Update Twilio webhook URLs if domain changed
```

### RTO Target: 2 hours  |  RPO Target: 24 hours (daily backups)

---

## 5. Backup / Restore Runbook

### Manual Backup

```bash
# Database
docker compose exec postgres pg_dump -U agent billing_agent > \
  /opt/backups/db_$(date +%Y%m%d_%H%M%S).sql

# Compress
gzip /opt/backups/db_*.sql
```

### Restore

```bash
# Stop application (prevent writes during restore)
docker compose stop backend

# Drop and recreate DB
docker compose exec postgres psql -U agent -c "DROP DATABASE billing_agent;"
docker compose exec postgres psql -U agent -c "CREATE DATABASE billing_agent;"

# Restore
gunzip -c /opt/backups/db_20260703_020000.sql.gz | \
  docker compose exec -T postgres psql -U agent billing_agent

# Restart
docker compose start backend
docker compose exec backend alembic upgrade head
curl https://your-domain.com/health/ready
```

---

## 6. Monitoring Runbook

### Key Alerts to Configure

| Alert | Condition | Action |
|-------|-----------|--------|
| Service down | `/health/ready` returns non-200 for > 2 min | Page on-call |
| High error rate | `http_requests_total{status=~"5.."} > 10/min` | Investigate logs |
| High latency | P95 > 5s for > 5 min | Check DB + Redis |
| DB connections exhausted | Pool usage > 90% | Increase pool / check N+1 |
| Redis memory > 80% | `redis_used_memory > 200MB` | Eviction check |
| Disk > 80% | `disk_percent > 80` | Clean old backups |

### Health Check Monitoring

```bash
# Simple uptime monitor (add to cron)
*/5 * * * * curl -sf https://your-domain.com/health/ready > /dev/null || \
  mail -s "ALERT: billing-agent down" ops@your-org.com
```

---

## 7. Scaling Runbook

### Vertical Scaling (increase resources)

```bash
# Update docker-compose.yml resources section
# Or upgrade EC2/VM instance size
# No code changes needed
```

### Horizontal Backend Scaling

Requires:
1. External Postgres (RDS/Cloud SQL) — not Docker Compose Postgres
2. External Redis (ElastiCache/Upstash) — not Docker Compose Redis
3. Load balancer with sticky sessions for WebSocket connections

```bash
# Scale to 3 backend replicas (Docker Swarm)
docker service scale billing-agent_backend=3
```

### Database Scaling

```bash
# Add read replica for analytics queries
# Update DATABASE_READ_URL in .env (future enhancement)

# Increase connection pool if pool exhausted
# DB_POOL_SIZE=30  (in .env)
```

---

## 8. Certificate Renewal Runbook

```bash
# Let's Encrypt auto-renewal (certbot installs a cron/systemd timer)
# Verify auto-renewal
certbot renew --dry-run

# Manual renewal
certbot renew
# Reload nginx after renewal
docker compose exec frontend nginx -s reload
```

---

## 9. Log Rotation

```bash
# Docker log size is unlimited by default — set limits in daemon.json
# /etc/docker/daemon.json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "100m",
    "max-file": "5"
  }
}
sudo systemctl restart docker
```
