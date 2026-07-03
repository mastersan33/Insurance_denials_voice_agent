from sqlalchemy import Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base, TimestampMixin, UUIDMixin


class BillingCase(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "billing_cases"

    patient_name: Mapped[str] = mapped_column(String(255))
    patient_dob: Mapped[str | None] = mapped_column(String(20), nullable=True)
    subscriber_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    payer_name: Mapped[str] = mapped_column(String(255), index=True)
    payer_phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    claim_number: Mapped[str] = mapped_column(String(100), index=True)
    service_date: Mapped[str | None] = mapped_column(String(20), nullable=True)
    cpt_codes: Mapped[str | None] = mapped_column(Text, nullable=True)
    icd10_codes: Mapped[str | None] = mapped_column(Text, nullable=True)
    amount_billed: Mapped[float | None] = mapped_column(Float, nullable=True)
    denial_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    denial_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    provider_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    provider_npi: Mapped[str | None] = mapped_column(String(20), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="open", index=True)
    priority: Mapped[str] = mapped_column(String(20), default="normal", index=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    call_jobs = relationship("CallJob", back_populates="billing_case", lazy="selectin")
