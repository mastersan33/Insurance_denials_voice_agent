import asyncio
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool

from backend.app.api.v1.router import api_router
from backend.app.config.logging import setup_logging
from backend.app.config.settings import settings
from backend.app.db.redis import close_redis
from backend.app.db.session import init_db
from backend.app.middleware.logging_middleware import RequestLoggingMiddleware
from backend.app.middleware.request_id import RequestIDMiddleware
from backend.app.middleware.security_headers import SecurityHeadersMiddleware
from backend.app.observability.metrics import PrometheusMiddleware, router as metrics_router
from backend.app.websocket.media_stream import router as ws_router
from backend.app.websocket.dashboard_ws import router as dashboard_ws_router


def _run_migrations() -> None:
    backend_dir = Path(__file__).resolve().parent.parent
    db_url = (
        settings.database_url
        .replace("sqlite+aiosqlite", "sqlite")
        .replace("postgresql+asyncpg", "postgresql+psycopg2")
    )

    engine = create_engine(db_url, poolclass=NullPool)
    with engine.connect() as conn:
        current = MigrationContext.configure(conn).get_current_revision()
    engine.dispose()

    alembic_cfg = Config(str(backend_dir / "alembic.ini"))
    alembic_cfg.set_main_option("script_location", str(backend_dir / "alembic"))
    alembic_cfg.set_main_option("sqlalchemy.url", db_url)

    head = ScriptDirectory.from_config(alembic_cfg).get_current_head()
    if current == head:
        return

    command.upgrade(alembic_cfg, "head")


def _validate_settings() -> None:
    """Fail fast if critical configuration is missing or insecure in production."""
    errors: list[str] = []

    if settings.environment == "production":
        if settings.secret_key == "change-me-in-production":
            errors.append("SECRET_KEY must be changed from the default value in production.")
        if not settings.twilio_account_sid:
            errors.append("TWILIO_ACCOUNT_SID is required in production.")
        if not settings.twilio_auth_token:
            errors.append("TWILIO_AUTH_TOKEN is required in production.")
        if not settings.elevenlabs_api_key:
            errors.append("ELEVENLABS_API_KEY is required in production.")
        if not settings.openai_api_key:
            errors.append("OPENAI_API_KEY is required in production.")

    if errors:
        for err in errors:
            print(f"[CONFIG ERROR] {err}", file=sys.stderr)
        raise RuntimeError(f"Startup aborted due to {len(errors)} configuration error(s).")


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    _validate_settings()
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, _run_migrations)
    await init_db()
    yield
    await close_redis()


_ALLOWED_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
_ALLOWED_HEADERS = ["Authorization", "Content-Type", "X-Request-ID"]

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs" if settings.environment != "production" else None,
    redoc_url="/redoc" if settings.environment != "production" else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=_ALLOWED_METHODS,
    allow_headers=_ALLOWED_HEADERS,
)
app.add_middleware(GZipMiddleware, minimum_size=1000)  # compress responses > 1KB
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(PrometheusMiddleware)

app.include_router(api_router)
app.include_router(metrics_router)
app.include_router(ws_router, prefix="/api/v1/twilio")
app.include_router(dashboard_ws_router)
