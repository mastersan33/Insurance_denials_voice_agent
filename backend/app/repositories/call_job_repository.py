from datetime import date, datetime, timezone

from sqlalchemy import func, select
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

    async def count_today_by_status(self, status: str) -> int:
        today_start = datetime.combine(date.today(), datetime.min.time()).replace(
            tzinfo=timezone.utc
        )
        result = await self.db.execute(
            select(func.count(CallJob.id)).where(
                CallJob.status == status,
                CallJob.created_at >= today_start,
            )
        )
        return result.scalar_one()

    async def count_today(self) -> int:
        today_start = datetime.combine(date.today(), datetime.min.time()).replace(
            tzinfo=timezone.utc
        )
        result = await self.db.execute(
            select(func.count(CallJob.id)).where(CallJob.created_at >= today_start)
        )
        return result.scalar_one()

    async def get_daily_counts(self, days: int = 7) -> list[dict]:
        """Return per-day totals/completed/failed for the last N days."""
        from datetime import timedelta

        results = []
        for i in range(days - 1, -1, -1):
            day = date.today() - timedelta(days=i)
            start = datetime.combine(day, datetime.min.time()).replace(tzinfo=timezone.utc)
            end = datetime.combine(day, datetime.max.time()).replace(tzinfo=timezone.utc)

            total = await self.db.execute(
                select(func.count(CallJob.id)).where(
                    CallJob.created_at >= start, CallJob.created_at <= end
                )
            )
            completed = await self.db.execute(
                select(func.count(CallJob.id)).where(
                    CallJob.status == "completed",
                    CallJob.created_at >= start,
                    CallJob.created_at <= end,
                )
            )
            failed = await self.db.execute(
                select(func.count(CallJob.id)).where(
                    CallJob.status == "failed",
                    CallJob.created_at >= start,
                    CallJob.created_at <= end,
                )
            )
            results.append(
                {
                    "date": day.isoformat(),
                    "total": total.scalar_one(),
                    "completed": completed.scalar_one(),
                    "failed": failed.scalar_one(),
                }
            )
        return results

    async def get_outcome_counts(self) -> list[dict]:
        result = await self.db.execute(
            select(CallJob.outcome, func.count(CallJob.id))
            .where(CallJob.outcome.isnot(None))
            .group_by(CallJob.outcome)
        )
        rows = result.all()
        total = sum(r[1] for r in rows) or 1
        return [
            {"outcome": r[0], "count": r[1], "percentage": round(r[1] / total * 100, 1)}
            for r in rows
        ]
