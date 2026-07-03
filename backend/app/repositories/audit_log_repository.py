from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.audit_log import AuditLog
from backend.app.repositories.base import BaseRepository


class AuditLogRepository(BaseRepository[AuditLog]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, AuditLog)

    async def search(
        self,
        actor_id: str | None = None,
        action: str | None = None,
        resource_type: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[AuditLog], int]:
        stmt = select(AuditLog).order_by(AuditLog.created_at.desc())
        count_stmt = select(func.count()).select_from(AuditLog)

        if actor_id:
            stmt = stmt.where(AuditLog.actor_id == actor_id)
            count_stmt = count_stmt.where(AuditLog.actor_id == actor_id)
        if action:
            stmt = stmt.where(AuditLog.action == action)
            count_stmt = count_stmt.where(AuditLog.action == action)
        if resource_type:
            stmt = stmt.where(AuditLog.resource_type == resource_type)
            count_stmt = count_stmt.where(AuditLog.resource_type == resource_type)

        total = (await self.db.execute(count_stmt)).scalar_one()
        rows = list((await self.db.execute(stmt.offset(skip).limit(limit))).scalars().all())
        return rows, total
