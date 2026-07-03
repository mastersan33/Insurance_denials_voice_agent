from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.models.call_session import CallSession
from backend.app.repositories.base import BaseRepository


class CallSessionRepository(BaseRepository[CallSession]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, CallSession)

    async def get_by_call_sid(self, call_sid: str) -> CallSession | None:
        result = await self.db.execute(
            select(CallSession).where(CallSession.twilio_call_sid == call_sid)
        )
        return result.scalar_one_or_none()

    async def get_active_sessions(self) -> list[CallSession]:
        result = await self.db.execute(
            select(CallSession).where(
                CallSession.status.in_(["initiated", "ringing", "in_progress"])
            )
        )
        return list(result.scalars().all())

    async def get_by_job_id(self, call_job_id: str) -> list[CallSession]:
        result = await self.db.execute(
            select(CallSession).where(CallSession.call_job_id == call_job_id)
        )
        return list(result.scalars().all())

    async def get_average_duration(self) -> float:
        result = await self.db.execute(
            select(func.avg(CallSession.duration_seconds)).where(
                CallSession.duration_seconds.isnot(None)
            )
        )
        return result.scalar_one() or 0.0

    async def get_recent_with_job(self, limit: int = 10) -> list[CallSession]:
        """Return recent sessions joined with their call_job (and billing case)."""
        result = await self.db.execute(
            select(CallSession)
            .options(
                selectinload(CallSession.call_job).selectinload(
                    # type: ignore[attr-defined]
                    CallSession.call_job.property.mapper.class_.billing_case
                )
            )
            .order_by(CallSession.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
