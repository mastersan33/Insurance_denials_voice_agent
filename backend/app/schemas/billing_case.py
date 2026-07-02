from datetime import datetime

from pydantic import BaseModel


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
    notes: str | None = None


class BillingCaseUpdate(BaseModel):
    patient_name: str | None = None
    payer_name: str | None = None
    payer_phone: str | None = None
    claim_number: str | None = None
    denial_code: str | None = None
    denial_reason: str | None = None
    status: str | None = None
    notes: str | None = None


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
    notes: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    class Config:
        from_attributes = True
