from enum import StrEnum


class CallStatus(StrEnum):
    QUEUED = "queued"
    INITIATED = "initiated"
    RINGING = "ringing"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BUSY = "busy"
    NO_ANSWER = "no_answer"
    CANCELED = "canceled"


class CallJobStatus(StrEnum):
    PENDING = "pending"
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"


class TicketStatus(StrEnum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    ESCALATED = "escalated"
    CLOSED = "closed"


class TicketPriority(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class AgentPhase(StrEnum):
    IVR_NAVIGATION = "ivr_navigation"
    AUTHENTICATION = "authentication"
    INFORMATION_GATHERING = "information_gathering"
    NEGOTIATION = "negotiation"
    RESOLUTION = "resolution"
    WRAP_UP = "wrap_up"


class HandoffReason(StrEnum):
    LOW_CONFIDENCE = "low_confidence"
    CALLER_REQUEST = "caller_request"
    COMPLEX_ISSUE = "complex_issue"
    ESCALATION = "escalation"
    REPEATED_FAILURE = "repeated_failure"


MAX_CALL_DURATION_SECONDS = 1800
MAX_IVR_ATTEMPTS = 10
CONFIDENCE_THRESHOLD = 0.6
