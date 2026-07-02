from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base, TimestampMixin, UUIDMixin


class Transcript(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "transcripts"

    call_session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("call_sessions.id"), index=True
    )
    speaker: Mapped[str] = mapped_column(String(20))  # "agent" or "human"
    content: Mapped[str] = mapped_column(Text)
    sequence_number: Mapped[int] = mapped_column(Integer)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    call_session = relationship("CallSession", back_populates="transcripts")
