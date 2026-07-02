from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base, TimestampMixin, UUIDMixin


class ConversationMemory(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "conversation_memories"

    call_session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("call_sessions.id"), index=True
    )
    role: Mapped[str] = mapped_column(String(20))  # system, user, assistant, tool
    content: Mapped[str] = mapped_column(Text)
    sequence_number: Mapped[int] = mapped_column(Integer)
    token_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)
