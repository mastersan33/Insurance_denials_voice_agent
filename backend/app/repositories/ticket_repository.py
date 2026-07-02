from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.ticket import Ticket
from backend.app.repositories.base import BaseRepository


class TicketRepository(BaseRepository[Ticket]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, Ticket)

    async def get_by_status(self, status: str, skip: int = 0, limit: int = 100) -> list[Ticket]:
        result = await self.db.execute(
            select(Ticket).where(Ticket.status == status).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def count_open(self) -> int:
        result = await self.db.execute(
            select(func.count(Ticket.id)).where(Ticket.status.in_(["open", "in_progress"]))
        )
        return result.scalar_one()
