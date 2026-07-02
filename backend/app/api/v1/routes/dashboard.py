from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.dependencies import CurrentUser
from backend.app.db.session import get_db
from backend.app.schemas.dashboard import DashboardStats
from backend.app.services.dashboard_service import DashboardService

router = APIRouter()


@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    _: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    service = DashboardService(db)
    return await service.get_stats()
