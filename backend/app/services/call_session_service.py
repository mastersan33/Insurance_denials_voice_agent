from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.call_session import CallSession
from backend.app.repositories.call_session_repository import CallSessionRepository
from backend.app.schemas.call_session import CallSessionResponse
from backend.app.core.exceptions import NotFoundException


class CallSessionService:
    def __init__(self, db: AsyncSession):
        self.repo = CallSessionRepository(db)

    async def create_session(self, call_job_id: str, from_number: str, to_number: str) -> CallSession:
        session = CallSession(
            call_job_id=call_job_id,
            from_number=from_number,
            to_number=to_number,
            status="initiated",
        )
        return await self.repo.create(session)

    async def get_session(self, session_id: str) -> CallSessionResponse:
        session = await self.repo.get_by_id(session_id)
        if not session:
            raise NotFoundException("CallSession", session_id)
        return CallSessionResponse.model_validate(session)

    async def get_by_call_sid(self, call_sid: str) -> CallSession | None:
        return await self.repo.get_by_call_sid(call_sid)

    async def get_active_sessions(self) -> list[CallSessionResponse]:
        sessions = await self.repo.get_active_sessions()
        return [CallSessionResponse.model_validate(s) for s in sessions]

    async def update_status(self, session_id: str, status: str, **kwargs) -> CallSession:
        session = await self.repo.get_by_id(session_id)
        if not session:
            raise NotFoundException("CallSession", session_id)
        data = {"status": status, **kwargs}
        return await self.repo.update(session, data)
