"""Audit log read API — write path is handled by audit_service.audit()."""
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.dependencies import CurrentUser, require_role
from backend.app.db.session import get_db
from backend.app.repositories.audit_log_repository import AuditLogRepository
from backend.app.schemas.billing_case import PaginatedResponse

router = APIRouter()


class AuditLogResponse:
    pass


@router.get("")
async def list_audit_logs(
    _: Annotated[None, require_role("supervisor")],
    db: Annotated[AsyncSession, Depends(get_db)],
    actor_id: str | None = None,
    action: str | None = None,
    resource_type: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
) -> dict:
    repo = AuditLogRepository(db)
    rows, total = await repo.search(
        actor_id=actor_id, action=action, resource_type=resource_type,
        skip=skip, limit=limit,
    )
    items = [
        {
            "id": r.id,
            "actor_id": r.actor_id,
            "actor_email": r.actor_email,
            "action": r.action,
            "resource_type": r.resource_type,
            "resource_id": r.resource_id,
            "ip_address": r.ip_address,
            "status": r.status,
            "detail": r.detail,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]
    return {"items": items, "total": total, "skip": skip, "limit": limit}
