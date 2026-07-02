from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.call_job import CallJob
from backend.app.repositories.base import BaseRepository


class CallJobRepository(BaseRepository[CallJob]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, CallJob)

    async def get_by_status(self, status: str, skip: int = 0, limit: int = 100) -> list[CallJob]:
        result = await self.db.execute(
            select(CallJob).where(CallJob.status == status).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def get_pending_jobs(self, limit: int = 10) -> list[CallJob]:
        result = await self.db.execute(
            select(CallJob)
            .where(CallJob.status == "pending")
            .order_by(CallJob.priority.desc(), CallJob.created_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_billing_case(self, billing_case_id: str) -> list[CallJob]:
        result = await self.db.execute(
            select(CallJob).where(CallJob.billing_case_id == billing_case_id)
        )
        return list(result.scalars().all())

    async def count_by_status(self, status: str) -> int:
        result = await self.db.execute(
            select(func.count(CallJob.id)).where(CallJob.status == status)
        )
        return result.scalar_one()
