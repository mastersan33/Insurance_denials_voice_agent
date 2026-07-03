"""Thin async helper for writing audit log entries.

Usage::

    from backend.app.services.audit_service import audit
    audit(actor=current_user, action="billing_case.create",
          resource_type="BillingCase", resource_id=case.id)
"""
from __future__ import annotations

from backend.app.db.session import async_session_factory
from backend.app.models.audit_log import AuditLog
from backend.app.models.user import User


async def _write_audit(
    actor_id: str | None,
    actor_email: str | None,
    action: str,
    resource_type: str | None,
    resource_id: str | None,
    ip_address: str | None,
    user_agent: str | None,
    status: str,
    detail: str | None,
    metadata: dict | None,
) -> None:
    try:
        async with async_session_factory() as db:
            db.add(AuditLog(
                actor_id=actor_id,
                actor_email=actor_email,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                ip_address=ip_address,
                user_agent=user_agent,
                status=status,
                detail=detail,
                metadata_=metadata,
            ))
            await db.commit()
    except Exception:
        pass


def audit(
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
    """Schedule an audit write as a background asyncio task (zero-latency, fire-and-forget)."""
    import asyncio
    _actor_id = (actor.id if actor else actor_id) or None
    _actor_email = (actor.email if actor else actor_email) or None
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(_write_audit(
            _actor_id, _actor_email, action, resource_type, resource_id,
            ip_address, user_agent, status, detail, metadata,
        ))
    except RuntimeError:
        # No running loop (e.g., sync test context) — skip silently
        pass
