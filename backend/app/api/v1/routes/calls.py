from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.dependencies import CurrentUser
from backend.app.db.session import get_db
from backend.app.schemas.call_session import CallSessionResponse
from backend.app.services.call_session_service import CallSessionService

router = APIRouter()


@router.get("/active", response_model=list[CallSessionResponse])
async def get_active_calls(
    _: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    service = CallSessionService(db)
    return await service.get_active_sessions()


@router.get("/{session_id}", response_model=CallSessionResponse)
async def get_call_session(
    session_id: str,
    _: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    service = CallSessionService(db)
    return await service.get_session(session_id)
