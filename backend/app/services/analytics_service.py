"""Analytics service — aggregates deeper metrics beyond the headline dashboard.

Performance notes:
- All per-day trend queries use a SINGLE SQL aggregation (DATE() group-by) instead
  of N separate queries per day. This reduces DB round-trips from O(N) to O(1).
- All results are cached in Redis with a 5-minute TTL.
"""
from datetime import date, datetime, timedelta, timezone
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.cache import ANALYTICS_TTL, cache
from backend.app.models.billing_case import BillingCase
from backend.app.models.call_job import CallJob
from backend.app.models.call_session import CallSession
from backend.app.models.transcript import Transcript


class AnalyticsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ── Internal helpers ───────────────────────────────────────────────────────

    @staticmethod
    def _window(days: int) -> datetime:
        """UTC datetime for start of window."""
        return datetime.now(timezone.utc) - timedelta(days=days)

    # ── Call volume (single batch query) ─────────────────────────────────────

    async def get_call_volume(self, days: int = 30) -> list[dict]:
        cache_key = cache.analytics_key("call_volume", days=days)
        if (hit := await cache.get_json(cache_key)) is not None:
            return hit

        since = self._window(days)

        # Single query: group by DATE(created_at)
        rows = (await self.db.execute(
            select(
                func.date(CallJob.created_at).label("day"),
                func.count(CallJob.id).label("total"),
                func.sum(case((CallJob.status == "completed", 1), else_=0)).label("completed"),
                func.sum(case((CallJob.status == "failed", 1), else_=0)).label("failed"),
            )
            .where(CallJob.created_at >= since)
            .group_by(func.date(CallJob.created_at))
            .order_by(func.date(CallJob.created_at))
        )).all()

        # Fill gaps with zeros for dates without data
        by_date: dict[str, dict] = {
            r.day: {"date": r.day, "total": r.total, "completed": r.completed, "failed": r.failed}
            for r in rows
        }
        result = []
        today = date.today()
        for i in range(days - 1, -1, -1):
            d = (today - timedelta(days=i)).isoformat()
            result.append(by_date.get(d, {"date": d, "total": 0, "completed": 0, "failed": 0}))

        await cache.set_json(cache_key, result, ttl=ANALYTICS_TTL)
        return result

    async def get_outcome_breakdown(self) -> list[dict]:
        cache_key = cache.analytics_key("outcomes")
        if (hit := await cache.get_json(cache_key)) is not None:
            return hit

        rows = (await self.db.execute(
            select(CallJob.outcome, func.count(CallJob.id))
            .where(CallJob.outcome.isnot(None))
            .group_by(CallJob.outcome)
        )).all()
        total = sum(r[1] for r in rows) or 1
        result = [{"outcome": r[0], "count": r[1], "percentage": round(r[1] / total * 100, 1)} for r in rows]
        await cache.set_json(cache_key, result, ttl=ANALYTICS_TTL)
        return result

    async def get_avg_duration_by_day(self, days: int = 14) -> list[dict]:
        cache_key = cache.analytics_key("avg_duration", days=days)
        if (hit := await cache.get_json(cache_key)) is not None:
            return hit

        since = self._window(days)
        rows = (await self.db.execute(
            select(
                func.date(CallSession.created_at).label("day"),
                func.avg(CallSession.duration_seconds).label("avg_duration"),
            )
            .where(
                CallSession.created_at >= since,
                CallSession.duration_seconds.isnot(None),
            )
            .group_by(func.date(CallSession.created_at))
            .order_by(func.date(CallSession.created_at))
        )).all()

        by_date = {r.day: round(r.avg_duration, 1) for r in rows}
        today = date.today()
        result = []
        for i in range(days - 1, -1, -1):
            d = (today - timedelta(days=i)).isoformat()
            result.append({"date": d, "avg_duration": by_date.get(d, 0)})

        await cache.set_json(cache_key, result, ttl=ANALYTICS_TTL)
        return result

    async def get_resolution_rate_trend(self, days: int = 14) -> list[dict]:
        cache_key = cache.analytics_key("resolution_trend", days=days)
        if (hit := await cache.get_json(cache_key)) is not None:
            return hit

        since = self._window(days)
        rows = (await self.db.execute(
            select(
                func.date(CallJob.created_at).label("day"),
                func.count(CallJob.id).label("total"),
                func.sum(case((CallJob.status == "completed", 1), else_=0)).label("completed"),
            )
            .where(CallJob.created_at >= since)
            .group_by(func.date(CallJob.created_at))
            .order_by(func.date(CallJob.created_at))
        )).all()

        by_date = {
            r.day: round(r.completed / r.total * 100, 1) if r.total else 0.0
            for r in rows
        }
        today = date.today()
        result = []
        for i in range(days - 1, -1, -1):
            d = (today - timedelta(days=i)).isoformat()
            result.append({"date": d, "rate": by_date.get(d, 0.0)})

        await cache.set_json(cache_key, result, ttl=ANALYTICS_TTL)
        return result

    async def get_payer_breakdown(self) -> list[dict]:
        cache_key = cache.analytics_key("payers")
        if (hit := await cache.get_json(cache_key)) is not None:
            return hit

        rows = (await self.db.execute(
            select(BillingCase.payer_name, func.count(BillingCase.id))
            .group_by(BillingCase.payer_name)
            .order_by(func.count(BillingCase.id).desc())
            .limit(10)
        )).all()
        total = sum(r[1] for r in rows) or 1
        result = [{"payer": r[0], "count": r[1], "percentage": round(r[1] / total * 100, 1)} for r in rows]
        await cache.set_json(cache_key, result, ttl=ANALYTICS_TTL)
        return result

    async def get_denial_code_breakdown(self) -> list[dict]:
        cache_key = cache.analytics_key("denial_codes")
        if (hit := await cache.get_json(cache_key)) is not None:
            return hit

        rows = (await self.db.execute(
            select(BillingCase.denial_code, func.count(BillingCase.id))
            .where(BillingCase.denial_code.isnot(None))
            .group_by(BillingCase.denial_code)
            .order_by(func.count(BillingCase.id).desc())
            .limit(10)
        )).all()
        total = sum(r[1] for r in rows) or 1
        result = [{"code": r[0], "count": r[1], "percentage": round(r[1] / total * 100, 1)} for r in rows]
        await cache.set_json(cache_key, result, ttl=ANALYTICS_TTL)
        return result

    async def get_summary(self) -> dict:
        cache_key = cache.analytics_key("summary")
        if (hit := await cache.get_json(cache_key)) is not None:
            return hit

        # Single pass: aggregate all statuses at once
        rows = (await self.db.execute(
            select(
                func.count(CallJob.id).label("total"),
                func.sum(case((CallJob.status == "completed", 1), else_=0)).label("completed"),
                func.sum(case((CallJob.status == "failed", 1), else_=0)).label("failed"),
            )
        )).one()

        avg_dur = (await self.db.execute(
            select(func.avg(CallSession.duration_seconds)).where(CallSession.duration_seconds.isnot(None))
        )).scalar_one() or 0

        total_transcripts = (await self.db.execute(select(func.count(Transcript.id)))).scalar_one()
        total_cases = (await self.db.execute(select(func.count(BillingCase.id)))).scalar_one()

        result = {
            "total_calls": rows.total,
            "completed_calls": rows.completed,
            "failed_calls": rows.failed,
            "resolution_rate": round(rows.completed / rows.total * 100, 1) if rows.total else 0.0,
            "avg_duration_seconds": round(avg_dur, 1),
            "total_transcript_turns": total_transcripts,
            "total_billing_cases": total_cases,
        }
        await cache.set_json(cache_key, result, ttl=ANALYTICS_TTL)
        return result

