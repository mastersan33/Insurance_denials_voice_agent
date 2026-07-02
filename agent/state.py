from typing import Annotated, TypedDict

from langgraph.graph import add_messages


class AgentState(TypedDict):
    """State for the billing voice agent conversation."""

    # Conversation messages
    messages: Annotated[list, add_messages]

    # Call metadata
    call_id: str
    call_sid: str
    call_job_id: str

    # Billing case context
    billing_case_id: str
    patient_name: str
    payer_name: str
    claim_number: str
    denial_code: str
    denial_reason: str

    # Current phase tracking
    current_phase: str  # ivr_navigation, authentication, gathering, negotiation, wrap_up
    phase_turn_count: int

    # Gathered information
    representative_name: str
    reference_number: str
    appeal_deadline: str
    appeal_method: str
    resolution_offered: str
    gathered_info: dict

    # Control flow
    confidence_score: float
    should_escalate: bool
    escalation_reason: str
    should_end_call: bool

    # IVR state
    ivr_attempts: int
    human_detected: bool

    # Response
    response_text: str
    dtmf_to_send: str
