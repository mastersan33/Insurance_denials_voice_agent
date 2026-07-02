from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.dependencies import CurrentUser
from backend.app.db.session import get_db
from backend.app.schemas.call_job import CallJobCreate, CallJobResponse, CallJobUpdate
from backend.app.services.call_job_service import CallJobService

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
