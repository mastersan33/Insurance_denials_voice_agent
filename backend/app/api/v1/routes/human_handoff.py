"""Human handoff management endpoints."""
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.dependencies import CurrentUser, require_role
from backend.app.core.exceptions import NotFoundException
from backend.app.db.session import get_db
from backend.app.models.human_handoff import HumanHandoff
from backend.app.repositories.human_handoff_repository import HumanHandoffRepository

router = APIRouter()

_VALID_STATUSES = {"pending", "assigned", "resolved"}


class HandoffUpdate(BaseModel):
    status: str | None = None
    resolution_notes: str | None = None
    assigned_to: str | None = None


@router.get("")
async def list_handoffs(
    _: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    status: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    repo = HumanHandoffRepository(db)
    if status == "pending":
        items = await repo.get_pending(skip, limit)
    else:
        stmt = select(HumanHandoff).order_by(HumanHandoff.created_at.desc()).offset(skip).limit(limit)
        if status:
            stmt = stmt.where(HumanHandoff.status == status)
        result = await db.execute(stmt)
        items = list(result.scalars().all())

    return [
        {
            "id": h.id,
            "call_session_id": h.call_session_id,
            "reason": h.reason,
            "context_summary": h.context_summary,
            "agent_phase": h.agent_phase,
            "confidence_at_handoff": h.confidence_at_handoff,
            "assigned_to": h.assigned_to,
            "status": h.status,
            "resolution_notes": h.resolution_notes,
            "created_at": h.created_at.isoformat() if h.created_at else None,
        }
        for h in items
    ]


@router.patch("/{handoff_id}")
async def update_handoff(
    handoff_id: str,
    data: HandoffUpdate,
    _: Annotated[None, require_role("operator")],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    repo = HumanHandoffRepository(db)
    handoff = await repo.get_by_id(handoff_id)
    if not handoff:
        raise NotFoundException("HumanHandoff", handoff_id)
    update_data = data.model_dump(exclude_none=True)
    handoff = await repo.update(handoff, update_data)
    return {
        "id": handoff.id,
        "status": handoff.status,
        "resolution_notes": handoff.resolution_notes,
        "assigned_to": handoff.assigned_to,
    }
