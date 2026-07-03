from pydantic import BaseModel


class CallVolumePoint(BaseModel):
    date: str       # YYYY-MM-DD
    total: int
    completed: int
    failed: int


class OutcomeBreakdown(BaseModel):
    outcome: str
    count: int
    percentage: float


class RecentCallActivity(BaseModel):
    id: str
    claim_number: str
    payer_name: str
    patient_name: str
    status: str
    outcome: str | None
    duration_seconds: int | None
    created_at: str


class QueueStatus(BaseModel):
    pending: int
    in_progress: int
    scheduled: int
    failed_retryable: int


class SystemHealthStatus(BaseModel):
    database: bool
    redis: bool
    twilio_configured: bool
    elevenlabs_configured: bool
    openai_configured: bool


class DashboardStats(BaseModel):
    # Headline metrics
    total_calls: int
    active_calls: int
    completed_calls: int
    failed_calls: int
    total_billing_cases: int
    open_tickets: int
    resolution_rate: float
    average_call_duration: float

    # Today's snapshot
    calls_today: int
    completed_today: int
    failed_today: int
    amount_recovered_today: float

    # Queue
    queue: QueueStatus

    # 7-day chart data
    call_volume_7d: list[CallVolumePoint]

    # Outcome breakdown (pie/donut)
    outcome_breakdown: list[OutcomeBreakdown]

    # Recent activity feed (last 10 calls)
    recent_activity: list[RecentCallActivity]

    # System health
    health: SystemHealthStatus
