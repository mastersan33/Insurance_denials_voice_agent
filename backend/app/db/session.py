from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.app.config.settings import settings

_is_sqlite = "sqlite" in settings.database_url
_engine_kwargs: dict = {"echo": settings.db_echo, "pool_pre_ping": not _is_sqlite}
if not _is_sqlite:
    _engine_kwargs["pool_size"] = settings.db_pool_size
    _engine_kwargs["max_overflow"] = settings.db_max_overflow

engine = create_async_engine(settings.database_url, **_engine_kwargs)

async_session_factory = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Import all models so SQLAlchemy's metadata is fully populated.

    Schema creation and migrations are handled exclusively by Alembic
    (``_run_migrations`` in main.py lifespan).  This function only ensures
    all ORM model classes are imported before the app starts serving requests,
    which is required for relationship loading and mapper configuration.
    """
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
    )
