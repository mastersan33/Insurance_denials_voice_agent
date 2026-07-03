from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config.settings import settings
from backend.app.repositories.billing_case_repository import BillingCaseRepository
from backend.app.repositories.call_job_repository import CallJobRepository
from backend.app.repositories.call_session_repository import CallSessionRepository
from backend.app.repositories.ticket_repository import TicketRepository
from backend.app.schemas.dashboard import (
    CallVolumePoint,
    DashboardStats,
    OutcomeBreakdown,
    QueueStatus,
    RecentCallActivity,
    SystemHealthStatus,
)


class DashboardService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.call_job_repo = CallJobRepository(db)
        self.session_repo = CallSessionRepository(db)
        self.billing_repo = BillingCaseRepository(db)
        self.ticket_repo = TicketRepository(db)

    async def get_stats(self) -> DashboardStats:
        # Headline counts
        total_calls = await self.call_job_repo.count()
        active_calls = await self.call_job_repo.count_by_status("in_progress")
        completed_calls = await self.call_job_repo.count_by_status("completed")
        failed_calls = await self.call_job_repo.count_by_status("failed")
        total_billing_cases = await self.billing_repo.count()
        open_tickets = await self.ticket_repo.count_open()
        avg_duration = await self.session_repo.get_average_duration()
        resolution_rate = (completed_calls / total_calls * 100) if total_calls > 0 else 0.0

        # Today
        calls_today = await self.call_job_repo.count_today()
        completed_today = await self.call_job_repo.count_today_by_status("completed")
        failed_today = await self.call_job_repo.count_today_by_status("failed")

        # Queue breakdown
        pending = await self.call_job_repo.count_by_status("pending")
        scheduled = await self.call_job_repo.count_by_status("scheduled")
        queue = QueueStatus(
            pending=pending,
            in_progress=active_calls,
            scheduled=scheduled,
            failed_retryable=failed_calls,
        )

        # 7-day chart
        daily_raw = await self.call_job_repo.get_daily_counts(days=7)
        call_volume_7d = [CallVolumePoint(**d) for d in daily_raw]

        # Outcome breakdown
        outcome_raw = await self.call_job_repo.get_outcome_counts()
        outcome_breakdown = [OutcomeBreakdown(**o) for o in outcome_raw]

        # Recent activity
        recent_sessions = await self.session_repo.get_recent_with_job(limit=10)
        recent_activity = []
        for s in recent_sessions:
            try:
                job = s.call_job
                case = job.billing_case if job else None
                recent_activity.append(
                    RecentCallActivity(
                        id=s.id,
                        claim_number=case.claim_number if case else "—",
                        payer_name=case.payer_name if case else "—",
                        patient_name=case.patient_name if case else "—",
                        status=s.status,
                        outcome=s.outcome,
                        duration_seconds=s.duration_seconds,
                        created_at=s.created_at.isoformat(),
                    )
                )
            except Exception:
                continue

        # System health
        health = SystemHealthStatus(
            database=True,  # If we got here, DB is up
            redis=await self._check_redis(),
            twilio_configured=bool(settings.twilio_account_sid and settings.twilio_auth_token),
            elevenlabs_configured=bool(settings.elevenlabs_api_key),
            openai_configured=bool(settings.openai_api_key),
        )

        return DashboardStats(
            total_calls=total_calls,
            active_calls=active_calls,
            completed_calls=completed_calls,
            failed_calls=failed_calls,
            total_billing_cases=total_billing_cases,
            open_tickets=open_tickets,
            resolution_rate=round(resolution_rate, 2),
            average_call_duration=round(avg_duration, 2),
            calls_today=calls_today,
            completed_today=completed_today,
            failed_today=failed_today,
            amount_recovered_today=0.0,  # Populated when payment tracking added
            queue=queue,
            call_volume_7d=call_volume_7d,
            outcome_breakdown=outcome_breakdown,
            recent_activity=recent_activity,
            health=health,
        )

    async def _check_redis(self) -> bool:
        try:
            from backend.app.db.redis import get_redis
            redis = await get_redis()
            await redis.ping()
            return True
        except Exception:
            return False
