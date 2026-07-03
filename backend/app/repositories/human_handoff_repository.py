from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.human_handoff import HumanHandoff
from backend.app.repositories.base import BaseRepository


class HumanHandoffRepository(BaseRepository[HumanHandoff]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, HumanHandoff)

    async def get_by_call_session(self, call_session_id: str) -> list[HumanHandoff]:
        result = await self.db.execute(
            select(HumanHandoff)
            .where(HumanHandoff.call_session_id == call_session_id)
            .order_by(HumanHandoff.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_pending(self, skip: int = 0, limit: int = 50) -> list[HumanHandoff]:
        result = await self.db.execute(
            select(HumanHandoff)
            .where(HumanHandoff.status == "pending")
            .order_by(HumanHandoff.created_at.asc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
