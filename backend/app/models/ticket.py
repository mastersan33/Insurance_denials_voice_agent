from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base, TimestampMixin, UUIDMixin


class Ticket(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "tickets"

    call_session_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("call_sessions.id"), nullable=True, index=True
    )
    billing_case_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("billing_cases.id"), nullable=True, index=True
    )
    assigned_to: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(500))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="open", index=True)
    priority: Mapped[str] = mapped_column(String(20), default="medium")
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    resolution: Mapped[str | None] = mapped_column(Text, nullable=True)
