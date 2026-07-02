from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.repositories.billing_case_repository import BillingCaseRepository
from backend.app.repositories.call_job_repository import CallJobRepository
from backend.app.repositories.call_session_repository import CallSessionRepository
from backend.app.repositories.ticket_repository import TicketRepository
from backend.app.schemas.dashboard import DashboardStats


class DashboardService:
    def __init__(self, db: AsyncSession):
        self.call_job_repo = CallJobRepository(db)
        self.session_repo = CallSessionRepository(db)
        self.billing_repo = BillingCaseRepository(db)
        self.ticket_repo = TicketRepository(db)

    async def get_stats(self) -> DashboardStats:
        total_calls = await self.call_job_repo.count()
        active_calls = await self.call_job_repo.count_by_status("in_progress")
        completed_calls = await self.call_job_repo.count_by_status("completed")
        failed_calls = await self.call_job_repo.count_by_status("failed")
        total_billing_cases = await self.billing_repo.count()
        open_tickets = await self.ticket_repo.count_open()
        avg_duration = await self.session_repo.get_average_duration()

        resolution_rate = (completed_calls / total_calls * 100) if total_calls > 0 else 0.0

        return DashboardStats(
            total_calls=total_calls,
            active_calls=active_calls,
            completed_calls=completed_calls,
            failed_calls=failed_calls,
            total_billing_cases=total_billing_cases,
            open_tickets=open_tickets,
            resolution_rate=round(resolution_rate, 2),
            average_call_duration=round(avg_duration, 2),
        )
