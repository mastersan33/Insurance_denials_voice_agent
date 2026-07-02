from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.exceptions import NotFoundException
from backend.app.models.call_job import CallJob
from backend.app.repositories.call_job_repository import CallJobRepository
from backend.app.schemas.call_job import CallJobCreate, CallJobResponse, CallJobUpdate


class CallJobService:
    def __init__(self, db: AsyncSession):
        self.repo = CallJobRepository(db)

    async def create_job(self, data: CallJobCreate, user_id: str) -> CallJobResponse:
        job = CallJob(
            billing_case_id=data.billing_case_id,
            created_by=user_id,
            phone_number=data.phone_number,
            priority=data.priority,
            max_attempts=data.max_attempts,
        )
        job = await self.repo.create(job)
        return CallJobResponse.model_validate(job)

    async def get_job(self, job_id: str) -> CallJobResponse:
        job = await self.repo.get_by_id(job_id)
        if not job:
            raise NotFoundException("CallJob", job_id)
        return CallJobResponse.model_validate(job)

    async def list_jobs(self, status: str | None = None, skip: int = 0, limit: int = 50) -> list[CallJobResponse]:
        if status:
            jobs = await self.repo.get_by_status(status, skip, limit)
        else:
            jobs = await self.repo.get_all(skip, limit)
        return [CallJobResponse.model_validate(j) for j in jobs]

    async def update_job(self, job_id: str, data: CallJobUpdate) -> CallJobResponse:
        job = await self.repo.get_by_id(job_id)
        if not job:
            raise NotFoundException("CallJob", job_id)
        job = await self.repo.update(job, data.model_dump(exclude_none=True))
        return CallJobResponse.model_validate(job)

    async def get_pending_jobs(self, limit: int = 10) -> list[CallJobResponse]:
        jobs = await self.repo.get_pending_jobs(limit)
        return [CallJobResponse.model_validate(j) for j in jobs]
