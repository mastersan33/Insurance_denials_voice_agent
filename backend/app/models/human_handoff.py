from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base, TimestampMixin, UUIDMixin


class HumanHandoff(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "human_handoffs"

    call_session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("call_sessions.id"), index=True
    )
    reason: Mapped[str] = mapped_column(String(100))
    context_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    agent_phase: Mapped[str | None] = mapped_column(String(50), nullable=True)
    confidence_at_handoff: Mapped[str | None] = mapped_column(String(10), nullable=True)
    assigned_to: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(50), default="pending")
    resolution_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
