# Outbound Billing Voice Agent

> **v1.0** — AI-powered outbound voice agent for automating insurance billing denial resolution via phone.

[![CI](https://github.com/your-org/billing-voice-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/your-org/billing-voice-agent/actions)

---

## What It Does

The agent automatically calls insurance payers on behalf of medical billing teams to resolve claim denials. It navigates IVR menus, authenticates, gathers information, negotiates resolutions, and escalates to humans when needed — all without manual intervention.

**Core flow:**
```
Billing Case Created → Call Job Queued → Twilio Outbound Call →
  ElevenLabs STT/TTS ↔ LangGraph Agent (GPT-4o) →
  IVR Navigation → Authentication → Info Gathering → Negotiation →
  Outcome Recorded → Human Escalation if needed
```

---

## Tech Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Backend | FastAPI + Python | 3.12 / 0.115 |
| Database | PostgreSQL (SQLite dev) | 16 |
| Cache | Redis | 7 |
| AI Agent | OpenAI GPT-4o + LangGraph | latest |
| Voice | Twilio Voice API + Media Streams | |
| STT/TTS | ElevenLabs Scribe + Turbo | |
| Frontend | React + TypeScript + Vite | 18.3 / 5.5 |
| State | TanStack Query v5 + Zustand | |
| Infra | Docker Compose + Nginx | |
| CI/CD | GitHub Actions | |

---

## Repository Layout

```
.
├── agent/                      # LangGraph voice agent
│   ├── config.py               # Agent tuning parameters
│   ├── graph.py                # State machine (planner → executor → observer)
│   ├── prompts.py              # Phase-specific system prompts
│   ├── state.py                # AgentState TypedDict
│   ├── tools.py                # Agent tool definitions
│   ├── memory.py               # Conversation memory manager
│   ├── outcomes.py             # Outcome classification
│   └── escalation.py          # Escalation logic
│
├── backend/
│   ├── app/
│   │   ├── api/v1/routes/      # All HTTP endpoints
│   │   ├── config/             # Settings, logging, constants
│   │   ├── core/               # Security, dependencies, exceptions
│   │   ├── db/                 # Async SQLAlchemy engine + Redis client
│   │   ├── elevenlabs/         # ElevenLabs STT/TTS WebSocket client
│   │   ├── middleware/         # Security headers, logging, request-id
│   │   ├── models/             # SQLAlchemy ORM models
│   │   ├── observability/      # Prometheus metrics
│   │   ├── repositories/       # Data access layer (Repository pattern)
│   │   ├── schemas/            # Pydantic request/response models
│   │   ├── services/           # Business logic layer
│   │   ├── tools/              # Backend agent tool implementations
│   │   ├── twilio/             # Twilio REST + Media Stream client
│   │   ├── utils/              # Shared utilities
│   │   ├── voice/              # Audio processing, transcript helpers
│   │   ├── websocket/          # WebSocket manager + dashboard push
│   │   └── main.py             # FastAPI app, lifespan, middleware
│   ├── alembic/                # Database migrations
│   │   └── versions/           # Migration history
│   └── tests/                  # pytest test suite
│
├── frontend/
│   └── src/
│       ├── components/         # Shared UI components
│       ├── hooks/              # React Query hooks
│       ├── layouts/            # Page layout wrappers
│       ├── pages/              # Full page components
│       ├── services/           # Axios API client + endpoints
│       ├── store/              # Zustand state stores
│       └── types/              # TypeScript type definitions
│
├── infra/
│   ├── docker/                 # Dockerfiles (backend + frontend)
│   ├── github/workflows/       # CI/CD pipeline
│   └── nginx/                  # Nginx reverse proxy config
│
├── scripts/
│   └── seed_db.py              # Development database seeder
│
├── docs/                       # Full documentation (see below)
├── docker-compose.yml          # One-command local stack
├── Makefile                    # Developer shortcuts
├── .env.example                # Environment variable template
└── ruff.toml / mypy.ini        # Code quality config
```

---

## Quick Start (Docker Compose)

```bash
# 1. Clone
git clone https://github.com/your-org/billing-voice-agent.git
cd billing-voice-agent

# 2. Configure environment
cp .env.example .env
# Edit .env — set SECRET_KEY, API keys, passwords

# 3. Start everything
docker compose up -d --build

# 4. Run migrations (first time)
docker compose exec backend alembic upgrade head

# 5. Seed development data (optional)
docker compose exec backend python -m scripts.seed_db

# 6. Open
#   Frontend:  http://localhost:3000
#   API docs:  http://localhost:8000/docs
#   Metrics:   http://localhost:8000/metrics
```

Default admin credentials (seeded): `admin@example.com` / `Admin123!`

---

## Local Development (without Docker)

**Prerequisites:** Python 3.12, Node 20, Redis running locally.

```bash
# Backend
pip install -r backend/requirements.txt -r backend/requirements-dev.txt
cp .env.example .env            # Set DATABASE_URL to SQLite (default)
alembic upgrade head
uvicorn backend.app.main:app --reload --port 8000

# Frontend (separate terminal)
cd frontend
npm install
npm run dev                     # http://localhost:5173
```

---

## Environment Variables

See [`.env.example`](.env.example) for the full list.

| Variable | Required | Description |
|----------|----------|-------------|
| `SECRET_KEY` | ✅ prod | JWT signing key — generate with `secrets.token_hex(32)` |
| `DATABASE_URL` | ✅ | PostgreSQL (prod) or SQLite (dev) |
| `REDIS_URL` | ✅ | Redis connection string with password |
| `OPENAI_API_KEY` | ✅ | GPT-4o API key |
| `TWILIO_ACCOUNT_SID` | ✅ | Twilio account identifier |
| `TWILIO_AUTH_TOKEN` | ✅ | Twilio auth token (used for webhook validation) |
| `TWILIO_PHONE_NUMBER` | ✅ | Outbound caller ID |
| `TWILIO_WEBHOOK_BASE_URL` | ✅ | Public HTTPS URL Twilio calls back to |
| `ELEVENLABS_API_KEY` | ✅ | ElevenLabs API key |
| `ELEVENLABS_VOICE_ID` | ✅ | Voice ID for TTS |
| `ENVIRONMENT` | | `local` / `dev` / `staging` / `production` |

---

## API

- **OpenAPI / Swagger:** http://localhost:8000/docs (disabled in production)
- **ReDoc:** http://localhost:8000/redoc
- **Base URL:** `/api/v1/`

| Category | Endpoints |
|----------|-----------|
| Auth | `POST /auth/login` `POST /auth/register` `POST /auth/refresh` `POST /auth/logout` |
| Billing Cases | `GET/POST /billing-cases` `GET/PATCH/DELETE /billing-cases/{id}` `POST /billing-cases/bulk-import` |
| Call Jobs | `GET/POST /call-jobs` `POST /call-jobs/{id}/trigger` `POST /call-jobs/{id}/cancel` |
| Calls | `GET /calls/active` `GET /calls/{id}` |
| Transcripts | `GET /transcripts/{session_id}` |
| Analytics | `GET /analytics/summary` `GET /analytics/call-volume` `GET /analytics/outcomes` |
| Dashboard | `GET /dashboard/stats` |
| Tickets | `GET/POST /tickets` `PATCH /tickets/{id}` |
| Human Handoff | `GET /human-handoff` `PATCH /human-handoff/{id}` |
| Users | `GET /users` `PATCH /users/{id}` `DELETE /users/{id}` |
| Reports | `GET /reports/billing-cases` `GET /reports/calls` |
| Audit | `GET /audit` |
| Health | `GET /health` `GET /health/ready` `GET /health/system` |

---

## WebSocket

| Endpoint | Auth | Description |
|----------|------|-------------|
| `ws://{host}/ws/dashboard?token={jwt}` | JWT query param | Real-time dashboard stat push |
| `ws://{host}/api/v1/twilio/media-stream/{call_id}` | Twilio signature | Media stream (Twilio → ElevenLabs → agent) |

---

## Roles & Permissions

| Role | Permissions |
|------|-------------|
| `viewer` | Read billing cases, calls, analytics |
| `operator` | + Create/trigger calls, manage tickets, resolve handoffs |
| `supervisor` | + Audit logs, reports, user list, cancel queue |
| `admin` | + User role changes, deactivate users, all destructive ops |

---

## Running Tests

```bash
pytest backend/tests/ -v --cov=backend --cov-report=term-missing
```

---

## Documentation

Full documentation lives in [`docs/`](docs/):

| Document | Description |
|----------|-------------|
| [`docs/architecture.md`](docs/architecture.md) | High-level system design |
| [`docs/api.md`](docs/api.md) | Complete API reference |
| [`docs/database.md`](docs/database.md) | Schema design & indexes |
| [`docs/ai-architecture.md`](docs/ai-architecture.md) | LangGraph agent design |
| [`docs/deployment.md`](docs/deployment.md) | Production deployment guide |
| [`docs/runbooks.md`](docs/runbooks.md) | Incident response & operations |
| [`docs/developer-guide.md`](docs/developer-guide.md) | Onboarding & coding standards |
| [`docs/security.md`](docs/security.md) | Security architecture & controls |
| [`docs/performance.md`](docs/performance.md) | Performance benchmarks & tuning |

---

## Security

- JWT access tokens (60 min) + HttpOnly cookie refresh tokens (30 days)
- bcrypt password hashing (cost 12)
- Twilio webhook signature validation on all `/twilio/*` endpoints
- RBAC (viewer → operator → supervisor → admin)
- Rate limiting: 10 login attempts/min, 5 registrations/hour per IP
- OWASP security headers on all responses
- All secrets via environment variables — never committed
- SQL injection prevention via SQLAlchemy parameterised queries
- XSS prevention via CSP headers + React's default escaping

---

## License

Proprietary — All rights reserved.


## Quick Start

### Prerequisites

- Python 3.12+
- Node.js 20+
- Docker & Docker Compose (for full stack)

### Option 1: Docker Compose (Recommended)

```bash
# Clone and configure
cp .env.example .env
# Edit .env with your API keys

# Start all services
docker compose up -d --build

# Backend: http://localhost:8000
# Frontend: http://localhost:3000
# API Docs: http://localhost:8000/docs
```

### Option 2: Local Development

```bash
# Backend
pip install -r backend/requirements.txt
cp .env.example .env  # Edit with your keys
uvicorn backend.app.main:app --reload

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

### Option 3: Make Commands

```bash
make install        # Install all dependencies
make dev-backend    # Start backend with hot reload
make dev-frontend   # Start frontend dev server
make test           # Run tests
make lint           # Run linter
make docker-up      # Start Docker stack
make docker-down    # Stop Docker stack
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/health` | Health check |
| POST | `/api/v1/auth/register` | Register user |
| POST | `/api/v1/auth/login` | Login |
| GET | `/api/v1/dashboard/stats` | Dashboard statistics |
| GET/POST | `/api/v1/billing-cases` | Billing cases CRUD |
| GET/POST | `/api/v1/call-jobs` | Call job management |
| GET | `/api/v1/calls/active` | Active call sessions |
| GET | `/api/v1/transcripts/{id}` | Call transcripts |
| GET/POST | `/api/v1/tickets` | Ticket management |
| POST | `/api/v1/twilio/voice/answer` | Twilio voice webhook |
| POST | `/api/v1/twilio/voice/status` | Twilio status callback |
| WS | `/api/v1/twilio/media-stream/{sid}` | Media stream WebSocket |

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | Database connection string | Yes |
| `REDIS_URL` | Redis connection string | Yes |
| `SECRET_KEY` | JWT signing key | Yes |
| `OPENAI_API_KEY` | OpenAI API key | Yes |
| `TWILIO_ACCOUNT_SID` | Twilio Account SID | Yes |
| `TWILIO_AUTH_TOKEN` | Twilio Auth Token | Yes |
| `TWILIO_PHONE_NUMBER` | Twilio phone number | Yes |
| `TWILIO_WEBHOOK_BASE_URL` | Public URL for webhooks | Yes |
| `ELEVENLABS_API_KEY` | ElevenLabs API key | Yes |
| `ELEVENLABS_VOICE_ID` | ElevenLabs voice ID | Yes |

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Frontend  │────▶│   Backend    │────▶│  PostgreSQL  │
│  (React)    │     │  (FastAPI)   │     └─────────────┘
└─────────────┘     │              │     ┌─────────────┐
                    │              │────▶│    Redis     │
┌─────────────┐     │              │     └─────────────┘
│   Twilio    │◀───▶│              │
│  (Voice)    │     │              │     ┌─────────────┐
└─────────────┘     │              │────▶│   OpenAI    │
                    │              │     └─────────────┘
┌─────────────┐     │              │     ┌─────────────┐
│ ElevenLabs  │◀───▶│              │────▶│  LangGraph  │
│  (STT/TTS)  │     └──────────────┘     └─────────────┘
└─────────────┘
```

## Running Tests

```bash
pytest backend/tests/ -v --cov=backend
```

## License

Private - All rights reserved.
