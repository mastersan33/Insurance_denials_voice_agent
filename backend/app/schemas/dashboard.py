from pydantic import BaseModel


class DashboardStats(BaseModel):
    total_calls: int
    active_calls: int
    completed_calls: int
    failed_calls: int
    total_billing_cases: int
    open_tickets: int
    resolution_rate: float
    average_call_duration: float
