from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.transcript import Transcript
from backend.app.repositories.base import BaseRepository


class TranscriptRepository(BaseRepository[Transcript]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, Transcript)

    async def get_by_session(self, call_session_id: str) -> list[Transcript]:
        result = await self.db.execute(
            select(Transcript)
            .where(Transcript.call_session_id == call_session_id)
            .order_by(Transcript.sequence_number.asc())
        )
        return list(result.scalars().all())
