from pydantic import BaseModel


class CallSessionResponse(BaseModel):
    id: str
    call_job_id: str
    twilio_call_sid: str | None = None
    status: str
    direction: str
    from_number: str | None = None
    to_number: str | None = None
    started_at: str | None = None
    ended_at: str | None = None
    duration_seconds: int | None = None
    agent_phase: str | None = None
    confidence_score: float | None = None
    outcome: str | None = None
    outcome_details: str | None = None
    error_message: str | None = None
    created_at: str | None = None

    class Config:
        from_attributes = True
