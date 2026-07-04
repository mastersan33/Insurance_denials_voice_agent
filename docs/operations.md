# Operations Guide

## Daily Operations

### Health Verification (every morning)

```bash
# System health
curl https://your-domain.com/health/ready

# Container status
docker compose ps

# Error check (last 1 hour)
docker compose logs --since=1h backend | grep '"level":"error"' | tail -20

# Active calls check
curl -H "Authorization: Bearer <admin_token>" \
  https://your-domain.com/api/v1/calls/active | jq '.length'
```

---

## Production Checklist

### Pre-Go-Live

- [ ] `.env` production values set (all secrets rotated from dev)
- [ ] `ENVIRONMENT=production`
- [ ] TLS certificate installed and verified
- [ ] `alembic upgrade head` applied to production DB
- [ ] Admin password changed from seed default
- [ ] Twilio webhooks pointed to production URL
- [ ] Twilio account has sufficient balance / usage limits configured
- [ ] ElevenLabs quota sufficient for expected call volume
- [ ] OpenAI rate limits appropriate for concurrent call load
- [ ] CORS origins set to production frontend domain only
- [ ] `/docs` endpoint disabled (automatic in production)
- [ ] Prometheus metrics scraping configured
- [ ] Log aggregation configured (ELK/Loki/CloudWatch)
- [ ] Database backups scheduled (daily minimum)
- [ ] Backup restore tested
- [ ] Incident response contacts documented
- [ ] PagerDuty / alerting configured

### Go-Live Verification

```bash
# 1. Create test billing case
curl -X POST https://your-domain.com/api/v1/billing-cases \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"patient_name":"Test Patient","payer_name":"Test Payer","claim_number":"TEST-001"}'

# 2. Verify analytics
curl -H "Authorization: Bearer <token>" \
  https://your-domain.com/api/v1/analytics/summary

# 3. Verify dashboard WebSocket (browser DevTools → Network → WS)

# 4. Place a test call (Twilio sandbox number)
```

---

## Security Checklist

### Monthly

- [ ] Rotate `SECRET_KEY` (requires all users to re-login)
- [ ] Rotate `TWILIO_AUTH_TOKEN`
- [ ] Review audit logs for unusual activity: `GET /api/v1/audit`
- [ ] Review user list for inactive accounts: `GET /api/v1/users`
- [ ] Check `pip audit` for vulnerable packages: `pip audit -r backend/requirements.txt`
- [ ] Verify TLS certificate expiry: `certbot certificates`

### After Any Incident

- [ ] Rotate all API keys that may have been exposed
- [ ] Review audit logs for the incident timeframe
- [ ] Force logout all users: `POST /api/v1/auth/logout-all` for each affected user

---

## Backup Checklist

### Daily

- [ ] PostgreSQL dump (`pg_dump`) stored with timestamp
- [ ] Compressed (gzip) and stored off-server (S3/GCS/remote)
- [ ] Backup file size is non-zero and larger than previous day (data is growing)
- [ ] Backup log shows no errors

### Weekly

- [ ] Test restore to a staging environment
- [ ] Verify restored data integrity

### Automated Backup Script

```bash
#!/bin/bash
# /opt/scripts/backup.sh
set -e
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR=/opt/backups
REMOTE_BUCKET=s3://your-backup-bucket/billing-agent

mkdir -p $BACKUP_DIR

# PostgreSQL dump
docker compose -f /opt/billing-agent/docker-compose.yml exec -T postgres \
  pg_dump -U agent billing_agent | gzip > $BACKUP_DIR/db_$DATE.sql.gz

# Upload to S3
aws s3 cp $BACKUP_DIR/db_$DATE.sql.gz $REMOTE_BUCKET/db_$DATE.sql.gz

# Delete local backups older than 7 days
find $BACKUP_DIR -name "db_*.sql.gz" -mtime +7 -delete

echo "Backup completed: db_$DATE.sql.gz"
```

---

## Maintenance Guide

### Database Maintenance

```bash
# Vacuum (reclaim space, update stats)
docker compose exec postgres psql -U agent billing_agent -c "VACUUM ANALYZE;"

# Check table sizes
docker compose exec postgres psql -U agent billing_agent -c "
  SELECT tablename, pg_size_pretty(pg_total_relation_size(tablename::regclass))
  FROM pg_tables WHERE schemaname='public'
  ORDER BY pg_total_relation_size(tablename::regclass) DESC;"

# Check index usage (drop unused indexes)
docker compose exec postgres psql -U agent billing_agent -c "
  SELECT indexrelname, idx_scan FROM pg_stat_user_indexes
  ORDER BY idx_scan ASC;"
```

### Redis Maintenance

```bash
# Check memory
docker compose exec redis redis-cli -a $REDIS_PASSWORD info memory

# Check key count
docker compose exec redis redis-cli -a $REDIS_PASSWORD dbsize

# Flush cache only (not auth tokens — they're in DB, not Redis)
docker compose exec redis redis-cli -a $REDIS_PASSWORD KEYS "dashboard:*" | xargs redis-cli DEL
```

### Log Cleanup

```bash
# Docker logs are auto-rotated if daemon.json is configured (see runbooks.md)
# Application logs: ship to external system; no rotation needed locally
```

---

## User Management

### Create Admin User (via seed script)

```bash
docker compose exec backend python -m scripts.seed_db
```

### Change User Role

```bash
curl -X PATCH https://your-domain.com/api/v1/users/{user_id} \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{"role": "supervisor"}'
```

### Deactivate User

```bash
curl -X DELETE https://your-domain.com/api/v1/users/{user_id} \
  -H "Authorization: Bearer <admin_token>"
```

### Force Logout User

Currently: deactivate user account (invalidates all future auth).
Token rotation: wait for access token to expire (max 60 min).

---

## Scaling Triggers

| Metric | Trigger | Action |
|--------|---------|--------|
| P95 latency > 2s | Sustained > 15 min | Add backend replicas |
| CPU > 80% | Sustained > 10 min | Vertical scale or add replicas |
| DB connections > 90% | Sustained > 5 min | Increase pool size or add PgBouncer |
| Redis memory > 80% | Any time | Increase Redis maxmemory |
| Active calls > 40 | Sustained | Upgrade Twilio + ElevenLabs limits |

---

## Release Notes — v1.0.0 (July 2026)

### Features
- Full outbound voice agent for insurance denial resolution
- LangGraph state machine: IVR navigation → authentication → info gathering → negotiation → wrap-up
- Real-time dashboard with WebSocket push updates
- Billing case management with bulk CSV import
- Call queue with priority scheduling and retry logic
- Human escalation/handoff workflow
- Ticket management system
- Analytics and reporting (CSV/JSON export)
- Audit log (supervisor+)
- User management (admin)
- JWT + HttpOnly cookie authentication
- RBAC (viewer / operator / supervisor / admin)

### Known Limitations
- WebSocket dashboard does not yet support cross-worker broadcast (requires Redis Pub/Sub for multi-instance deployments)
- Bulk import validation is basic — malformed rows are skipped without per-row error reporting
- ElevenLabs STT confidence is used as a proxy but not perfectly calibrated for medical terminology
- No built-in scheduled calling (cron-based triggers) — calls must be manually triggered or via API
- Phone number validation is basic (no carrier lookup or line type detection)

### Security Notes
- Swagger UI (`/docs`) is disabled in production (`ENVIRONMENT=production`)
- Default seed credentials must be changed immediately after first deployment
- Twilio signature validation is skipped if `TWILIO_AUTH_TOKEN` is empty (local dev only)
