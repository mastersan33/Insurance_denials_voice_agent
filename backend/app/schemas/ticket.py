from pydantic import BaseModel


class TicketCreate(BaseModel):
    call_session_id: str | None = None
    billing_case_id: str | None = None
    title: str
    description: str | None = None
    priority: str = "medium"
    category: str | None = None


class TicketUpdate(BaseModel):
    status: str | None = None
    priority: str | None = None
    assigned_to: str | None = None
    resolution: str | None = None


class TicketResponse(BaseModel):
    id: str
    call_session_id: str | None = None
    billing_case_id: str | None = None
    assigned_to: str | None = None
    title: str
    description: str | None = None
    status: str
    priority: str
    category: str | None = None
    resolution: str | None = None
    created_at: str | None = None
    updated_at: str | None = None

    class Config:
        from_attributes = True
