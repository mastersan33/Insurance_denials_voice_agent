from datetime import datetime

from pydantic import BaseModel


class CallJobCreate(BaseModel):
    billing_case_id: str
    phone_number: str
    priority: int = 0
    max_attempts: int = 3
    scheduled_at: str | None = None


class CallJobUpdate(BaseModel):
    status: str | None = None
    priority: int | None = None
    outcome: str | None = None
    outcome_notes: str | None = None


class CallJobResponse(BaseModel):
    id: str
    billing_case_id: str
    created_by: str
    phone_number: str
    status: str
    priority: int
    max_attempts: int
    attempt_count: int
    scheduled_at: datetime | None = None
    completed_at: datetime | None = None
    outcome: str | None = None
    outcome_notes: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    class Config:
        from_attributes = True
