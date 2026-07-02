# Outbound Billing Voice Agent

AI-powered outbound voice agent for insurance billing denial resolution. Automates phone calls to insurance companies to resolve claim denials.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12, FastAPI, SQLAlchemy 2.0, Alembic |
| Database | PostgreSQL 16 (SQLite for local dev) |
| Cache | Redis 7 |
| AI | OpenAI GPT-4o, LangGraph, LangChain |
| Voice | Twilio Voice API, Twilio Media Streams |
| STT/TTS | ElevenLabs |
| Frontend | React 18, TypeScript, Vite, TailwindCSS |
| State | Zustand, TanStack React Query |
| DevOps | Docker, Docker Compose, GitHub Actions |

## Project Structure

```
├── backend/
│   ├── app/
│   │   ├── api/v1/routes/     # API endpoints
│   │   ├── config/            # Settings, logging, constants
│   │   ├── core/              # Security, dependencies, exceptions
│   │   ├── db/                # Database session, Redis
│   │   ├── models/            # SQLAlchemy models
│   │   ├── schemas/           # Pydantic schemas
│   │   ├── repositories/      # Data access layer
│   │   ├── services/          # Business logic
│   │   ├── twilio/            # Twilio client
│   │   ├── elevenlabs/        # ElevenLabs STT/TTS client
│   │   ├── websocket/         # WebSocket manager + media stream
│   │   └── main.py            # FastAPI application
│   ├── alembic/               # Database migrations
│   └── tests/                 # pytest test suite
├── agent/
│   ├── graph.py               # LangGraph state machine
│   ├── state.py               # Agent state definition
│   ├── prompts.py             # Prompt templates
│   ├── tools.py               # Agent tools
│   ├── memory.py              # Conversation memory manager
│   └── config.py              # Agent configuration
├── frontend/
│   └── src/
│       ├── components/        # Reusable UI components
│       ├── pages/             # Page components
│       ├── layouts/           # Layout wrappers
│       ├── hooks/             # React Query hooks
│       ├── services/          # API client
│       └── store/             # Zustand stores
├── infra/
│   ├── docker/                # Dockerfiles
│   ├── nginx/                 # Nginx config
│   └── github/workflows/      # CI/CD pipeline
├── docker-compose.yml
├── Makefile
└── .env.example
```

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
