from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, field_validator

T = TypeVar("T")


class BillingCaseCreate(BaseModel):
    patient_name: str
    patient_dob: str | None = None
    subscriber_id: str | None = None
    payer_name: str
    payer_phone: str | None = None
    claim_number: str
    service_date: str | None = None
    cpt_codes: str | None = None
    icd10_codes: str | None = None
    amount_billed: float | None = None
    denial_code: str | None = None
    denial_reason: str | None = None
    provider_name: str | None = None
    provider_npi: str | None = None
    priority: str = "normal"
    notes: str | None = None

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: str) -> str:
        if v not in ("low", "normal", "high", "urgent"):
            raise ValueError("priority must be low, normal, high, or urgent")
        return v


class BillingCaseUpdate(BaseModel):
    patient_name: str | None = None
    payer_name: str | None = None
    payer_phone: str | None = None
    claim_number: str | None = None
    denial_code: str | None = None
    denial_reason: str | None = None
    status: str | None = None
    priority: str | None = None
    notes: str | None = None

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: str | None) -> str | None:
        if v is not None and v not in ("low", "normal", "high", "urgent"):
            raise ValueError("priority must be low, normal, high, or urgent")
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str | None) -> str | None:
        if v is not None and v not in ("open", "in_progress", "resolved", "closed", "appealing"):
            raise ValueError("invalid status")
        return v


class BillingCaseResponse(BaseModel):
    id: str
    patient_name: str
    patient_dob: str | None = None
    subscriber_id: str | None = None
    payer_name: str
    payer_phone: str | None = None
    claim_number: str
    service_date: str | None = None
    cpt_codes: str | None = None
    icd10_codes: str | None = None
    amount_billed: float | None = None
    denial_code: str | None = None
    denial_reason: str | None = None
    provider_name: str | None = None
    provider_npi: str | None = None
    status: str
    priority: str
    notes: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    skip: int
    limit: int
