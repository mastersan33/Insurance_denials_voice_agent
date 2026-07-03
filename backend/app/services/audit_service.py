"""Thin async helper for writing audit log entries.

Usage::

    from backend.app.services.audit_service import audit
    await audit(db, actor=current_user, action="billing_case.create",
                resource_type="BillingCase", resource_id=case.id)
"""
from __future__ import annotations

from backend.app.db.session import async_session_factory
from backend.app.models.audit_log import AuditLog
from backend.app.models.user import User


async def audit(
    action: str,
    *,
    actor: User | None = None,
    actor_id: str | None = None,
    actor_email: str | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    status: str = "success",
    detail: str | None = None,
    metadata: dict | None = None,
) -> None:
    """Write an audit entry in a fresh DB session (fire-and-forget safe)."""
    _actor_id = (actor.id if actor else actor_id) or None
    _actor_email = (actor.email if actor else actor_email) or None

    try:
        async with async_session_factory() as db:
            entry = AuditLog(
                actor_id=_actor_id,
                actor_email=_actor_email,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                ip_address=ip_address,
                user_agent=user_agent,
                status=status,
                detail=detail,
                metadata_=metadata,
            )
            db.add(entry)
            await db.commit()
    except Exception:
        pass  # Never let audit failures break the main flow
