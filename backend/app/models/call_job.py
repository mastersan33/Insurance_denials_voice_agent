from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base, TimestampMixin, UUIDMixin


class CallJob(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "call_jobs"

    billing_case_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("billing_cases.id"), index=True
    )
    created_by: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), index=True
    )
    phone_number: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(50), default="pending", index=True)
    priority: Mapped[int] = mapped_column(Integer, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, default=3)
    attempt_count: Mapped[int] = mapped_column(Integer, default=0)
    scheduled_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)
    outcome: Mapped[str | None] = mapped_column(String(50), nullable=True)
    outcome_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    billing_case = relationship("BillingCase", back_populates="call_jobs")
    created_by_user = relationship("User", back_populates="call_jobs")
    sessions = relationship("CallSession", back_populates="call_job", lazy="selectin")
