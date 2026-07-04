# Deployment Guide

## Prerequisites

- Docker + Docker Compose installed on target server
- Domain name with DNS pointed to server IP
- TLS certificate (Let's Encrypt recommended)
- PostgreSQL 16 accessible (or use Docker Compose Postgres)
- Redis 7 accessible (or use Docker Compose Redis)

---

## First Deployment

### 1. Server Setup

```bash
# Ubuntu 22.04 / 24.04
sudo apt update && sudo apt install -y docker.io docker-compose-v2 git
sudo usermod -aG docker $USER
# Log out and back in
```

### 2. Clone Repository

```bash
git clone https://github.com/your-org/billing-voice-agent.git /opt/billing-agent
cd /opt/billing-agent
```

### 3. Configure Environment

```bash
cp .env.example .env
nano .env
```

Critical values to set:
```bash
ENVIRONMENT=production
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
DATABASE_URL=postgresql+asyncpg://agent:STRONG_PASSWORD@postgres:5432/billing_agent
POSTGRES_PASSWORD=STRONG_PASSWORD
REDIS_URL=redis://:REDIS_PASSWORD@redis:6379/0
REDIS_PASSWORD=REDIS_PASSWORD
OPENAI_API_KEY=sk-...
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...
TWILIO_PHONE_NUMBER=+1...
TWILIO_WEBHOOK_BASE_URL=https://your-domain.com
ELEVENLABS_API_KEY=...
ELEVENLABS_VOICE_ID=...
CORS_ORIGINS=["https://your-domain.com"]
FRONTEND_URL=https://your-domain.com
```

### 4. TLS Setup (Let's Encrypt)

```bash
# Install certbot
sudo snap install --classic certbot
sudo certbot certonly --standalone -d your-domain.com

# Certificates at:
# /etc/letsencrypt/live/your-domain.com/fullchain.pem
# /etc/letsencrypt/live/your-domain.com/privkey.pem
```

Update `infra/nginx/nginx.conf` to add SSL (or use an upstream load balancer for TLS termination).

### 5. Build and Start

```bash
docker compose up -d --build
```

### 6. Database Migrations

```bash
docker compose exec backend alembic upgrade head
```

### 7. Seed Initial Admin User

```bash
docker compose exec backend python -m scripts.seed_db
# Creates: admin@example.com / Admin123!
# CHANGE THIS PASSWORD IMMEDIATELY after first login
```

### 8. Verify

```bash
# Health check
curl https://your-domain.com/api/v1/health

# Readiness check
curl https://your-domain.com/health/ready

# Expected: {"status": "ready", "checks": {"database": true, "redis": true}}
```

---

## Subsequent Deployments

```bash
cd /opt/billing-agent

# Pull latest code
git pull origin main

# Rebuild and restart (zero-downtime if you have multiple replicas)
docker compose build
docker compose up -d

# Apply any new migrations
docker compose exec backend alembic upgrade head

# Verify health
curl https://your-domain.com/health/ready
```

---

## Zero-Downtime Deployment

For production, use rolling restarts:

```bash
# Build new image without stopping current
docker compose build backend

# Restart one instance at a time (if using multiple replicas via Docker Swarm / Kubernetes)
docker compose up -d --no-deps backend
```

---

## Docker Compose Services

| Service | Port | Description |
|---------|------|-------------|
| `backend` | 8000 | FastAPI + Uvicorn |
| `frontend` | 3000 → 80 | React (Nginx) |
| `postgres` | 5432 | PostgreSQL 16 |
| `redis` | 6379 | Redis 7 |

All services have health checks. Backend waits for healthy Postgres + Redis before starting.

---

## Environment-Specific Docker Compose Files

For staging, override values:
```bash
docker compose -f docker-compose.yml -f docker-compose.staging.yml up -d
```

---

## Scaling

### Horizontal Backend Scaling

```yaml
# docker-compose.override.yml
services:
  backend:
    deploy:
      replicas: 3
```

WebSocket connections require sticky sessions if using multiple backend replicas (configure in load balancer).

### Database Connection Pool

Set in `.env`:
```
DB_POOL_SIZE=20       # Per worker
DB_MAX_OVERFLOW=10
```

For 4 workers × 20 pool = 80 max connections to Postgres.
Postgres default `max_connections=100` — adjust `postgresql.conf` accordingly.

---

## Backup

### PostgreSQL

```bash
# Manual backup
docker compose exec postgres pg_dump -U agent billing_agent > backup_$(date +%Y%m%d).sql

# Restore
docker compose exec -T postgres psql -U agent billing_agent < backup_20260703.sql
```

### Automated backups (cron)

```bash
# /etc/cron.d/billing-agent-backup
0 2 * * * root cd /opt/billing-agent && docker compose exec -T postgres pg_dump -U agent billing_agent | gzip > /opt/backups/db_$(date +\%Y\%m\%d).sql.gz
```

---

## Monitoring

### Prometheus Metrics

Endpoint: `GET /metrics` (Prometheus format)

Scrape config:
```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'billing-agent'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: '/metrics'
```

Key metrics:
- `http_requests_total` — request count by method/path/status
- `http_request_duration_seconds` — latency histogram
- `active_websocket_connections` — WebSocket gauge
- `llm_response_duration_seconds` — AI latency
- `call_pipeline_duration_seconds` — end-to-end call latency

### Log Aggregation

Logs are structured JSON (structlog). Ship to ELK/Loki/CloudWatch:

```bash
# View live logs
docker compose logs -f backend

# All logs include:
# - request_id (correlation ID)
# - timestamp, level, event
# - method, path, status_code, duration_ms, client_ip
```

---

## Twilio Webhook Configuration

After deployment, configure Twilio to call your webhooks:

1. Log in to [Twilio Console](https://console.twilio.com)
2. Go to Phone Numbers → Your number
3. Set Voice webhook: `https://your-domain.com/api/v1/twilio/voice`
4. Set Status callback: `https://your-domain.com/api/v1/twilio/status`
5. Method: `POST`

---

## Production Checklist

- [ ] `ENVIRONMENT=production` in `.env`
- [ ] `SECRET_KEY` is a 64-byte random value
- [ ] All default passwords changed
- [ ] TLS certificate installed and auto-renewal configured
- [ ] Alembic migrations applied (`alembic upgrade head`)
- [ ] Admin password changed from seed default
- [ ] Twilio webhooks configured to production URL
- [ ] `/docs` endpoint is disabled (automatic when `ENVIRONMENT=production`)
- [ ] CORS origins locked to production domain
- [ ] Redis auth enabled (REDIS_PASSWORD set)
- [ ] Database backups scheduled
- [ ] Health check URL verified: `GET /health/ready`
- [ ] Prometheus metrics scraping configured
- [ ] Log aggregation configured
- [ ] Firewall: ports 5432 and 6379 closed to public internet
