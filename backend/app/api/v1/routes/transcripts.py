from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.dependencies import CurrentUser
from backend.app.db.session import get_db
from backend.app.models.transcript import Transcript
from backend.app.repositories.transcript_repository import TranscriptRepository
from backend.app.schemas.transcript import TranscriptResponse

router = APIRouter()


@router.get("/list", response_model=list[TranscriptResponse])
async def list_transcripts(
    _: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    result = await db.execute(
        select(Transcript).order_by(Transcript.created_at.desc()).offset(skip).limit(limit)
    )
    return [TranscriptResponse.model_validate(t) for t in result.scalars().all()]


@router.get("/{session_id}", response_model=list[TranscriptResponse])
async def get_transcripts(
    session_id: str,
    _: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    repo = TranscriptRepository(db)
    transcripts = await repo.get_by_session(session_id)
    return [TranscriptResponse.model_validate(t) for t in transcripts]
