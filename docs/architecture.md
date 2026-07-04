# Architecture Guide

## System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         INTERNET                                    │
└────────────────┬──────────────────────────────┬────────────────────┘
                 │                              │
         ┌───────▼──────┐              ┌────────▼───────┐
         │  Twilio      │              │  Browser       │
         │  (Voice API) │              │  (React SPA)   │
         └───────┬──────┘              └────────┬───────┘
                 │                              │
         ┌───────▼──────────────────────────────▼───────┐
         │              Nginx (reverse proxy)            │
         │  /api/* → backend:8000                        │
         │  /ws/*  → backend:8000 (WebSocket upgrade)   │
         │  /*     → React static bundle                 │
         └───────────────────────┬───────────────────────┘
                                 │
         ┌───────────────────────▼───────────────────────┐
         │                FastAPI Backend                  │
         │                                                 │
         │  ┌─────────────┐  ┌───────────────────────┐   │
         │  │ HTTP Routes │  │  WebSocket Handlers    │   │
         │  │  /api/v1/*  │  │  /ws/dashboard         │   │
         │  │             │  │  /api/v1/twilio/media  │   │
         │  └──────┬──────┘  └──────────┬─────────────┘   │
         │         │                    │                  │
         │  ┌──────▼──────────────────────────────────┐   │
         │  │            Service Layer                  │   │
         │  │  AuthService  CallJobService  AuditSvc   │   │
         │  └──────┬──────────────────────────────────┘   │
         │         │                                       │
         │  ┌──────▼──────────────────────────────────┐   │
         │  │          Repository Layer (DAL)           │   │
         │  └──────┬──────────────────────────────────┘   │
         │         │                                       │
         └─────────┼───────────────────────────────────────┘
                   │
          ┌────────┼────────┐
          │        │        │
   ┌──────▼──┐ ┌───▼───┐ ┌──▼──────────────────────────┐
   │PostgreSQL│ │ Redis │ │     LangGraph Agent          │
   │  (data) │ │(cache)│ │  planner→executor→observer   │
   └─────────┘ └───────┘ │  GPT-4o + ElevenLabs STT/TTS │
                          └──────────────────────────────┘
```

## Component Responsibilities

### Nginx
- TLS termination
- Reverse proxy to FastAPI
- Static file serving (React bundle)
- WebSocket upgrade handling
- Security headers (X-Frame-Options, CSP, HSTS)
- Rate limiting (optional — can add `limit_req_zone` for DDoS protection)

### FastAPI Backend
- HTTP API (REST)
- WebSocket servers (dashboard push, Twilio media stream)
- Middleware stack: RequestID → PrometheusMiddleware → SecurityHeaders → RequestLogging → CORS → GZip
- Lifespan: auto-migrations on startup, Redis disconnect on shutdown
- Stateless — all state in PostgreSQL + Redis

### LangGraph Agent (Voice Pipeline)
- Triggered per call session
- Three nodes: `planner` (assess state, check escalation) → `executor` (LLM response) → `observer` (phase transitions)
- Phase sequence: `ivr_navigation → authentication → information_gathering → negotiation → wrap_up`
- Escalates to human on: low confidence, phase timeout, explicit trigger
- Memory: stored in `conversation_memory` table per session

### PostgreSQL
- Primary datastore
- All business entities: billing_cases, call_jobs, call_sessions, transcripts, users, tickets, etc.
- Async access via `asyncpg` + SQLAlchemy 2.0

### Redis
- Login rate limiting (`ratelimit:login:{ip}`)
- Registration rate limiting (`ratelimit:register:{ip}`)
- Dashboard stat caching
- Analytics caching
- Session/health caching

### Twilio
- Outbound call initiation via REST API
- Media Stream WebSocket (bidirectional audio)
- Webhook callbacks: call status, recording events
- Signature validation on all webhook endpoints

### ElevenLabs
- Real-time STT via Scribe v1 WebSocket
- Real-time TTS via Turbo v2.5 WebSocket
- Audio streamed directly from Twilio media stream

---

## Data Flow: Outbound Call

```
1. User creates BillingCase → UI POST /billing-cases
2. Call Job created → POST /call-jobs (status: pending)
3. User triggers call → POST /call-jobs/{id}/trigger
4. Backend dials Twilio REST API → Twilio initiates call
5. Twilio connects → POST /api/v1/twilio/voice (TwiML response)
6. TwiML opens Media Stream → WS /api/v1/twilio/media-stream/{call_id}
7. Media stream handler:
   a. Receives μ-law audio from Twilio
   b. Converts to PCM 16kHz
   c. Sends to ElevenLabs STT WebSocket
   d. On transcript received → feeds to LangGraph agent
   e. Agent generates response text
   f. Response sent to ElevenLabs TTS WebSocket
   g. TTS audio returned → converted back to μ-law
   h. Sent back to Twilio → played to payer rep
8. Each turn updates CallSession state in DB
9. On call end → outcomes recorded, HumanHandoff created if escalated
10. Dashboard WebSocket pushes updated stats to all connected browsers
```

---

## Security Architecture

See [`docs/security.md`](security.md) for full details.

**Key controls:**
- Stateless JWT (access 60min) + opaque refresh token (30 days, HttpOnly cookie, SHA-256 hashed in DB)
- Twilio HMAC-SHA1 signature validation on all webhooks
- RBAC (4 levels: viewer < operator < supervisor < admin)
- All HTTP security headers (CSP, HSTS, X-Frame-Options, etc.)
- SQL injection: parameterised queries only via SQLAlchemy ORM

---

## Deployment Topology (Production)

```
              [Cloudflare / Load Balancer]
                        │
              [Nginx Container] ← TLS terminated here
                        │
              ┌─────────┴──────────┐
    [Backend Container × N]    [Frontend Container]
              │
    ┌─────────┴──────────┐
[PostgreSQL RDS]    [Redis ElastiCache]
```

---

## High-Level Design Decisions

| Decision | Choice | Reason |
|----------|--------|--------|
| ORM | SQLAlchemy async | Type-safe, async, standard Python |
| Agent framework | LangGraph | Explicit state machine, conditional edges, debuggable |
| Voice | Twilio Media Streams | Low-latency bidirectional audio |
| STT/TTS | ElevenLabs | Best-in-class quality for medical context |
| Auth tokens | JWT + opaque refresh | JWT for stateless auth checks, opaque refresh for revocability |
| Cache | Redis | Sub-ms latency, rate limiting, pub/sub capable |
| DB migrations | Alembic | Industry standard, reversible |
| Frontend | Vite + React 18 | Fast HMR, lazy code splitting |
</content>
</invoke>