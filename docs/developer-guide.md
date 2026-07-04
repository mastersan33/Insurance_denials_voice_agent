# Developer Guide

## Prerequisites

| Tool | Minimum Version | Install |
|------|----------------|---------|
| Python | 3.12 | [python.org](https://python.org) |
| Node.js | 20 LTS | [nodejs.org](https://nodejs.org) |
| Docker Desktop | 4.x | [docker.com](https://docker.com) |
| Git | 2.x | |

---

## Local Setup (15 minutes)

### Option A: Docker Compose (recommended)

```bash
git clone https://github.com/your-org/billing-voice-agent.git
cd billing-voice-agent

cp .env.example .env
# Edit .env — at minimum set:
#   SECRET_KEY (generate: python -c "import secrets; print(secrets.token_hex(32))")
#   OPENAI_API_KEY
#   TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER
#   ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID

docker compose up -d --build
docker compose exec backend alembic upgrade head
docker compose exec backend python -m scripts.seed_db

# Frontend: http://localhost:3000
# API:      http://localhost:8000/docs
# Login:    admin@example.com / Admin123!
```

### Option B: Native (faster iteration)

```bash
# Python environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r backend/requirements.txt -r backend/requirements-dev.txt

# Configuration (SQLite — no Postgres/Redis needed for basic dev)
cp .env.example .env
# DATABASE_URL=sqlite+aiosqlite:///./app.db  (already the default)

# Database
cd backend && alembic upgrade head && cd ..

# Seed data
PYTHONPATH=. python -m scripts.seed_db

# Start backend
PYTHONPATH=. uvicorn backend.app.main:app --reload --port 8000

# Frontend (separate terminal)
cd frontend && npm install && npm run dev
# http://localhost:5173
```

---

## Project Commands (Makefile)

```bash
make help            # Show all commands
make install         # Install all dependencies
make dev-backend     # Run backend with hot reload
make dev-frontend    # Run frontend dev server
make test            # Run pytest with coverage
make lint            # Run ruff linter
make typecheck       # Run mypy
make format          # Auto-format code
make migrate         # Apply pending migrations
make migrate-create MSG="add column x"  # Create new migration
make seed            # Seed dev database
make docker-up       # Start Docker Compose stack
make docker-down     # Stop Docker Compose stack
make docker-logs     # Tail Docker logs
```

---

## Running Tests

```bash
# All tests
pytest backend/tests/ -v

# With coverage report
pytest backend/tests/ --cov=backend --cov-report=term-missing

# Single file
pytest backend/tests/test_api.py -v -k "test_login"

# Fast (no coverage)
pytest backend/tests/ -x --no-header -q
```

Tests use:
- SQLite in-memory (`:memory:`) — no database setup needed
- `pytest-asyncio` with `asyncio_mode = auto`
- Isolated per test (no shared mutable state)

---

## Code Style

### Python
- **Formatter:** `ruff format` (black-compatible)
- **Linter:** `ruff check`
- **Types:** `mypy` — strict where possible, no bare `Any`
- **Async:** All I/O is async. Never use sync blocking calls in FastAPI handlers.

Conventions:
```python
# Good — async repository method
async def get_by_id(self, id: str) -> User | None:
    result = await self.db.execute(select(User).where(User.id == id))
    return result.scalar_one_or_none()

# Bad — sync call inside async context
def get_by_id(self, id: str) -> User | None:
    return self.db.execute(...)  # blocks event loop
```

### TypeScript / React
- **Strict mode** enabled in `tsconfig.json`
- No implicit `any`
- All Tailwind classes use design tokens (`text-foreground` not `text-gray-900`)
- One component per file
- `useQuery` / `useMutation` from `@tanstack/react-query` for all server state
- Zustand only for truly client-side state (auth, theme)

---

## Architecture Patterns

### Backend: Controller → Service → Repository

```
route (controller)
  └── calls service
        └── calls repository
              └── executes SQL via SQLAlchemy
```

- **Routes** validate input (via Pydantic) and return HTTP responses. No business logic.
- **Services** contain business logic. Can call multiple repositories.
- **Repositories** are the only place that touches the database.

### Frontend: Page → Hook → Service → API

```
Page component
  └── useQuery / useMutation (hook in useQueries.ts)
        └── calls endpoint function (endpoints.ts)
              └── axios API client (api.ts)
```

---

## Adding a New API Endpoint

1. Add Pydantic schema to `backend/app/schemas/`
2. Add repository method to `backend/app/repositories/`
3. Add service method to `backend/app/services/` (if business logic needed)
4. Add route to `backend/app/api/v1/routes/`
5. Register in `backend/app/api/v1/router.py`
6. Add frontend hook to `frontend/src/hooks/useQueries.ts`
7. Add endpoint function to `frontend/src/services/endpoints.ts`
8. Write a test in `backend/tests/`

---

## Adding a Database Column

```bash
# 1. Modify the SQLAlchemy model
# backend/app/models/billing_case.py

# 2. Generate migration
make migrate-create MSG="add_xyz_to_billing_cases"

# 3. Review the generated file in backend/alembic/versions/

# 4. Apply
make migrate
```

**Rule:** New columns must be `nullable=True` in the first migration.

---

## Twilio Local Testing

Use `ngrok` to expose your local server:

```bash
ngrok http 8000
# Copy the HTTPS URL → set TWILIO_WEBHOOK_BASE_URL in .env
```

Test Twilio signature validation:
```bash
# Valid (no signature — skipped in local dev when TWILIO_AUTH_TOKEN is empty)
curl -X POST http://localhost:8000/api/v1/twilio/voice \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "CallSid=CA123&CallStatus=initiated"

# Invalid signature (TWILIO_AUTH_TOKEN must be set to test this)
curl -X POST http://localhost:8000/api/v1/twilio/voice \
  -H "X-Twilio-Signature: invalid" \
  # → HTTP 403
```

---

## Git Workflow

```
main           Production-ready. Protected. PR required.
  │
develop        Integration branch. All features merge here first.
  │
feature/*      New features. Branch from develop.
fix/*          Bug fixes.
hotfix/*       Urgent production fixes. Branch from main.
```

Commit message format:
```
feat: add bulk import for billing cases
fix: correct pagination offset on tickets
chore: update alembic migration for audit logs
docs: add deployment guide
test: add tests for auth rate limiting
```

---

## Environment-Specific Behaviour

| Feature | local | dev | staging | production |
|---------|-------|-----|---------|-----------|
| SQLite DB | ✅ default | ❌ | ❌ | ❌ |
| /docs endpoint | ✅ | ✅ | ✅ | ❌ |
| HSTS header | ❌ | ❌ | ❌ | ✅ |
| Debug mode | settable | ❌ | ❌ | ❌ |
| Twilio sig validation | ❌ (if no token) | ✅ | ✅ | ✅ |
| Real LLM calls | configurable | ✅ | ✅ | ✅ |
