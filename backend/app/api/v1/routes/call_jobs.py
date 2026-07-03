from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.dependencies import CurrentUser
from backend.app.db.cache import cache
from backend.app.db.session import get_db
from backend.app.schemas.call_job import CallJobCreate, CallJobResponse, CallJobUpdate
from backend.app.schemas.call_session import CallSessionResponse
from backend.app.services.call_job_service import CallJobService
from backend.app.services.call_session_service import CallSessionService
from backend.app.config.settings import settings
from backend.app.twilio.client import twilio_client

router = APIRouter()


@router.get("", response_model=list[CallJobResponse])
async def list_call_jobs(
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    status: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    service = CallJobService(db)
    return await service.list_jobs(status, skip, limit)


@router.post("", response_model=CallJobResponse, status_code=201)
async def create_call_job(
    data: CallJobCreate,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    service = CallJobService(db)
    return await service.create_job(data, user.id)


@router.get("/pending", response_model=list[CallJobResponse])
async def get_pending_jobs(
    _: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(10, ge=1, le=50),
):
    service = CallJobService(db)
    return await service.get_pending_jobs(limit)


@router.get("/{job_id}", response_model=CallJobResponse)
async def get_call_job(
    job_id: str,
    _: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    service = CallJobService(db)
    return await service.get_job(job_id)


@router.patch("/{job_id}", response_model=CallJobResponse)
async def update_call_job(
    job_id: str,
    data: CallJobUpdate,
    _: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    service = CallJobService(db)
    return await service.update_job(job_id, data)


@router.post("/{job_id}/trigger", response_model=CallSessionResponse, status_code=201)
async def trigger_call(
    job_id: str,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Trigger an outbound call for a pending call job."""
    job_service = CallJobService(db)
    session_service = CallSessionService(db)

    job = await job_service.get_job(job_id)
    if job.status not in ("pending", "failed"):
        raise HTTPException(status_code=400, detail=f"Job status is '{job.status}', must be pending or failed to trigger.")

    call_sid = await twilio_client.initiate_call(to_number=job.phone_number)

    session = await session_service.create_session(
        call_job_id=job_id,
        from_number=settings.twilio_phone_number,
        to_number=job.phone_number,
    )
    await session_service.update_status(session.id, "initiated", twilio_call_sid=call_sid)
    await job_service.update_job(job_id, CallJobUpdate(status="in_progress"))
    await cache.invalidate(cache.dashboard_key())
    return CallSessionResponse.model_validate(session)


@router.post("/{job_id}/cancel", response_model=CallJobResponse)
async def cancel_call_job(
    job_id: str,
    _: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Cancel a pending or failed call job."""
    job_service = CallJobService(db)
    job = await job_service.get_job(job_id)
    if job.status not in ("pending", "failed", "scheduled", "paused"):
        raise HTTPException(status_code=400, detail=f"Cannot cancel job with status '{job.status}'.")
    return await job_service.update_job(job_id, CallJobUpdate(status="cancelled"))


@router.post("/queue/pause", response_model=dict)
async def pause_queue(
    _: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Pause all pending jobs in the queue."""
    service = CallJobService(db)
    result = await service.pause_queue()
    await db.commit()
    return result


@router.post("/queue/resume", response_model=dict)
async def resume_queue(
    _: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Resume all paused jobs."""
    service = CallJobService(db)
    result = await service.resume_queue()
    await db.commit()
    return result


@router.post("/queue/cancel-all", response_model=dict)
async def cancel_all_queue(
    _: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Cancel all pending, paused, and scheduled jobs."""
    service = CallJobService(db)
    result = await service.cancel_queue()
    await db.commit()
    return result


@router.post("/queue/retry-failed", response_model=dict)
async def retry_failed_jobs(
    _: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Requeue all retryable failed jobs."""
    service = CallJobService(db)
    result = await service.retry_failed()
    await db.commit()
    return result

