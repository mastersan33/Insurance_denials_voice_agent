"""Analytics service — aggregates deeper metrics beyond the headline dashboard."""
from datetime import date, datetime, timedelta, timezone
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.call_job import CallJob
from backend.app.models.call_session import CallSession
from backend.app.models.billing_case import BillingCase
from backend.app.models.transcript import Transcript


class AnalyticsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_call_volume(self, days: int = 30) -> list[dict]:
        results = []
        today = date.today()
        for i in range(days - 1, -1, -1):
            day = today - timedelta(days=i)
            start = datetime.combine(day, datetime.min.time()).replace(tzinfo=timezone.utc)
            end = datetime.combine(day, datetime.max.time()).replace(tzinfo=timezone.utc)

            total = (await self.db.execute(
                select(func.count(CallJob.id)).where(CallJob.created_at >= start, CallJob.created_at <= end)
            )).scalar_one()
            completed = (await self.db.execute(
                select(func.count(CallJob.id)).where(
                    CallJob.status == "completed", CallJob.created_at >= start, CallJob.created_at <= end
                )
            )).scalar_one()
            failed = (await self.db.execute(
                select(func.count(CallJob.id)).where(
                    CallJob.status == "failed", CallJob.created_at >= start, CallJob.created_at <= end
                )
            )).scalar_one()
            results.append({"date": day.isoformat(), "total": total, "completed": completed, "failed": failed})
        return results

    async def get_outcome_breakdown(self) -> list[dict]:
        rows = (await self.db.execute(
            select(CallJob.outcome, func.count(CallJob.id))
            .where(CallJob.outcome.isnot(None))
            .group_by(CallJob.outcome)
        )).all()
        total = sum(r[1] for r in rows) or 1
        return [{"outcome": r[0], "count": r[1], "percentage": round(r[1] / total * 100, 1)} for r in rows]

    async def get_avg_duration_by_day(self, days: int = 14) -> list[dict]:
        results = []
        today = date.today()
        for i in range(days - 1, -1, -1):
            day = today - timedelta(days=i)
            start = datetime.combine(day, datetime.min.time()).replace(tzinfo=timezone.utc)
            end = datetime.combine(day, datetime.max.time()).replace(tzinfo=timezone.utc)
            avg = (await self.db.execute(
                select(func.avg(CallSession.duration_seconds)).where(
                    CallSession.created_at >= start, CallSession.created_at <= end,
                    CallSession.duration_seconds.isnot(None),
                )
            )).scalar_one() or 0
            results.append({"date": day.isoformat(), "avg_duration": round(avg, 1)})
        return results

    async def get_resolution_rate_trend(self, days: int = 14) -> list[dict]:
        results = []
        today = date.today()
        for i in range(days - 1, -1, -1):
            day = today - timedelta(days=i)
            start = datetime.combine(day, datetime.min.time()).replace(tzinfo=timezone.utc)
            end = datetime.combine(day, datetime.max.time()).replace(tzinfo=timezone.utc)
            total = (await self.db.execute(
                select(func.count(CallJob.id)).where(CallJob.created_at >= start, CallJob.created_at <= end)
            )).scalar_one()
            completed = (await self.db.execute(
                select(func.count(CallJob.id)).where(
                    CallJob.status == "completed", CallJob.created_at >= start, CallJob.created_at <= end
                )
            )).scalar_one()
            rate = round(completed / total * 100, 1) if total > 0 else 0.0
            results.append({"date": day.isoformat(), "rate": rate})
        return results

    async def get_payer_breakdown(self) -> list[dict]:
        rows = (await self.db.execute(
            select(BillingCase.payer_name, func.count(BillingCase.id))
            .group_by(BillingCase.payer_name)
            .order_by(func.count(BillingCase.id).desc())
            .limit(10)
        )).all()
        total = sum(r[1] for r in rows) or 1
        return [{"payer": r[0], "count": r[1], "percentage": round(r[1] / total * 100, 1)} for r in rows]

    async def get_denial_code_breakdown(self) -> list[dict]:
        rows = (await self.db.execute(
            select(BillingCase.denial_code, func.count(BillingCase.id))
            .where(BillingCase.denial_code.isnot(None))
            .group_by(BillingCase.denial_code)
            .order_by(func.count(BillingCase.id).desc())
            .limit(10)
        )).all()
        total = sum(r[1] for r in rows) or 1
        return [{"code": r[0], "count": r[1], "percentage": round(r[1] / total * 100, 1)} for r in rows]

    async def get_summary(self) -> dict:
        total_calls = (await self.db.execute(select(func.count(CallJob.id)))).scalar_one()
        completed = (await self.db.execute(
            select(func.count(CallJob.id)).where(CallJob.status == "completed")
        )).scalar_one()
        failed = (await self.db.execute(
            select(func.count(CallJob.id)).where(CallJob.status == "failed")
        )).scalar_one()
        avg_dur = (await self.db.execute(
            select(func.avg(CallSession.duration_seconds)).where(CallSession.duration_seconds.isnot(None))
        )).scalar_one() or 0
        total_transcripts = (await self.db.execute(select(func.count(Transcript.id)))).scalar_one()
        total_cases = (await self.db.execute(select(func.count(BillingCase.id)))).scalar_one()
        return {
            "total_calls": total_calls,
            "completed_calls": completed,
            "failed_calls": failed,
            "resolution_rate": round(completed / total_calls * 100, 1) if total_calls else 0.0,
            "avg_duration_seconds": round(avg_dur, 1),
            "total_transcript_turns": total_transcripts,
            "total_billing_cases": total_cases,
        }
