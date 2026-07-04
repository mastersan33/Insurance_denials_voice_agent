"""Test configuration with isolated in-memory SQLite database.

Each test session gets a fresh in-memory SQLite database so tests never
touch the development ``app.db`` and run in full isolation.
"""
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.app.db.base import Base
from backend.app.db.session import get_db

# --------------------------------------------------------------------------- #
# Isolated async SQLite engine (shared for the entire test session)           #
# --------------------------------------------------------------------------- #

_TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

_test_engine = create_async_engine(
    _TEST_DB_URL,
    echo=False,
    connect_args={"check_same_thread": False},
)
_TestSessionFactory = async_sessionmaker(
    _test_engine, class_=AsyncSession, expire_on_commit=False
)


@pytest.fixture(scope="session", autouse=True)
async def _create_test_schema():
    """Create all tables once for the whole test session."""
    # Ensure all model classes are imported before create_all
    from backend.app.models import (  # noqa: F401
        billing_case,
        call_event,
        call_job,
        call_session,
        conversation_memory,
        human_handoff,
        ticket,
        transcript,
        user,
        audit_log,
    )
    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await _test_engine.dispose()


@pytest.fixture(autouse=True)
async def _rollback_after_test():
    """Wrap every test in a savepoint and roll it back afterwards."""
    async with _test_engine.connect() as conn:
        await conn.begin()
        session = AsyncSession(bind=conn, expire_on_commit=False)
        await conn.begin_nested()  # SAVEPOINT

        yield session

        await session.close()
        await conn.rollback()


@pytest.fixture
async def client(_rollback_after_test: AsyncSession):
    """HTTP test client wired to the isolated test database."""
    from backend.app.main import app

    async def _override_get_db():
        yield _rollback_after_test

    app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture
async def auth_headers(client: AsyncClient) -> dict:
    """Register + login a test admin user and return Authorization headers."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "testadmin@example.com",
            "password": "TestPass123!",
            "full_name": "Test Admin",
            "role": "admin",
        },
    )
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "testadmin@example.com", "password": "TestPass123!"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def auth_headers(client: AsyncClient):
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "password": "testpass123",
            "full_name": "Test User",
        },
    )
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "testpass123"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
