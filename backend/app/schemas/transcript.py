from datetime import datetime

from pydantic import BaseModel


class TranscriptResponse(BaseModel):
    id: str
    call_session_id: str
    speaker: str
    content: str
    sequence_number: int
    confidence: float | None = None
    duration_ms: int | None = None
    created_at: datetime | None = None

    class Config:
        from_attributes = True
