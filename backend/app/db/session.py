from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.app.config.settings import settings

engine = create_async_engine(
    settings.database_url,
    echo=settings.db_echo,
    pool_pre_ping=True,
    pool_size=settings.db_pool_size if "sqlite" not in settings.database_url else 5,
    max_overflow=settings.db_max_overflow if "sqlite" not in settings.database_url else 0,
)

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
    from backend.app.db.base import Base
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

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
