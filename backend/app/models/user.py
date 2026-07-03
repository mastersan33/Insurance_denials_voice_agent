from datetime import datetime

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base, TimestampMixin, UUIDMixin


class User(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(50), default="operator")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    organization_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    call_jobs = relationship("CallJob", back_populates="created_by_user", lazy="selectin")
    refresh_tokens = relationship(
        "RefreshToken", back_populates="user", lazy="raise", cascade="all, delete-orphan"
    )
