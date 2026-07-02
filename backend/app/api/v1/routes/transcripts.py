from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.dependencies import CurrentUser
from backend.app.db.session import get_db
from backend.app.repositories.transcript_repository import TranscriptRepository
from backend.app.schemas.transcript import TranscriptResponse

router = APIRouter()


@router.get("/{session_id}", response_model=list[TranscriptResponse])
async def get_transcripts(
    session_id: str,
    _: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    repo = TranscriptRepository(db)
    transcripts = await repo.get_by_session(session_id)
    return [TranscriptResponse.model_validate(t) for t in transcripts]
