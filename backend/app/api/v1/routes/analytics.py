from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.dependencies import CurrentUser
from backend.app.db.session import get_db
from backend.app.services.analytics_service import AnalyticsService

router = APIRouter()


@router.get("/summary")
async def get_analytics_summary(
    _: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    return await AnalyticsService(db).get_summary()


@router.get("/call-volume")
async def get_call_volume(
    _: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    days: int = Query(30, ge=7, le=90),
) -> list[dict]:
    return await AnalyticsService(db).get_call_volume(days)


@router.get("/outcomes")
async def get_outcome_breakdown(
    _: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[dict]:
    return await AnalyticsService(db).get_outcome_breakdown()


@router.get("/avg-duration")
async def get_avg_duration(
    _: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    days: int = Query(14, ge=7, le=90),
) -> list[dict]:
    return await AnalyticsService(db).get_avg_duration_by_day(days)


@router.get("/resolution-trend")
async def get_resolution_trend(
    _: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    days: int = Query(14, ge=7, le=90),
) -> list[dict]:
    return await AnalyticsService(db).get_resolution_rate_trend(days)


@router.get("/payers")
async def get_payer_breakdown(
    _: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[dict]:
    return await AnalyticsService(db).get_payer_breakdown()


@router.get("/denial-codes")
async def get_denial_code_breakdown(
    _: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[dict]:
    return await AnalyticsService(db).get_denial_code_breakdown()
