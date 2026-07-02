from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base, TimestampMixin, UUIDMixin


class CallSession(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "call_sessions"

    call_job_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("call_jobs.id"), index=True
    )
    twilio_call_sid: Mapped[str | None] = mapped_column(String(100), unique=True, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="initiated", index=True)
    direction: Mapped[str] = mapped_column(String(20), default="outbound")
    from_number: Mapped[str | None] = mapped_column(String(20), nullable=True)
    to_number: Mapped[str | None] = mapped_column(String(20), nullable=True)
    started_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ended_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    recording_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    agent_phase: Mapped[str | None] = mapped_column(String(50), nullable=True)
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    outcome: Mapped[str | None] = mapped_column(String(50), nullable=True)
    outcome_details: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    call_job = relationship("CallJob", back_populates="sessions")
    events = relationship("CallEvent", back_populates="call_session", lazy="selectin")
    transcripts = relationship("Transcript", back_populates="call_session", lazy="selectin")
