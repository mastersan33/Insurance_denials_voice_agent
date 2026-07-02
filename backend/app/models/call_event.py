from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base, TimestampMixin, UUIDMixin


class CallEvent(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "call_events"

    call_session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("call_sessions.id"), index=True
    )
    event_type: Mapped[str] = mapped_column(String(50), index=True)
    event_data: Mapped[str | None] = mapped_column(Text, nullable=True)
    phase: Mapped[str | None] = mapped_column(String(50), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    call_session = relationship("CallSession", back_populates="events")
