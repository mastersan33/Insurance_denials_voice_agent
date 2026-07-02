"""Escalation policy and handoff summary for the billing voice agent.

Day 10 requirement:
- Caller says 'human' → immediate escalation
- Identity verification fails twice → automatic escalation
- Handoff row must contain case_id, reason, summary, transcript

The EscalationPolicy is also used by the LangGraph graph (agent/graph.py)
via the `should_escalate` flag.
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class EscalationReason(str, Enum):
    CALLER_REQUESTED_HUMAN = "caller_requested_human"
    FAILED_IDENTITY_VERIFICATION = "failed_identity_verification"
    BILLING_DISPUTE = "billing_dispute"
    PAYMENT_NEGOTIATION = "payment_negotiation"
    INSURANCE_ESCALATION = "insurance_escalation"
    COMPLEX_ACCOUNT_QUESTION = "complex_account_question"
    CUSTOMER_FRUSTRATION = "customer_frustration"
    MEDICAL_OR_CLINICAL_REQUEST = "medical_or_clinical_request"
    MISSING_REQUIRED_INFORMATION = "missing_required_information"
    REPEATED_TOOL_FAILURE = "repeated_tool_failure"
    AGENT_UNCERTAIN = "agent_uncertain"
    COMPLIANCE_RISK = "compliance_risk"
    PHASE_TIMEOUT = "phase_timeout"


class EscalationDecision(BaseModel):
    should_escalate: bool
    reason: Optional[EscalationReason] = None
    priority: str = "low"
    caller_message: str = ""
    internal_note: str = ""
    recommended_destination: str = "billing_queue"
    safe_to_continue_with_ai: bool = True


class HandoffSummary(BaseModel):
    call_session_id: str
    case_id: Optional[str] = None
    claim_number: Optional[str] = None
    payer_name: Optional[str] = None
    patient_name: Optional[str] = None
    escalation_reason: Optional[str] = None
    priority: str = "low"
    conversation_summary: str
    collected_information: Dict[str, Any] = Field(default_factory=dict)
    missing_information: List[str] = Field(default_factory=list)
    tool_calls: List[Dict[str, Any]] = Field(default_factory=list)
    last_agent_message: Optional[str] = None
    recommended_next_action: str = "Review with senior billing specialist"
    compliance_notes: List[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# Trigger phrases for each escalation reason — checked in order
_TRIGGER_MAP: List[tuple[EscalationReason, tuple[str, ...]]] = [
    (
        EscalationReason.CALLER_REQUESTED_HUMAN,
        ("human", "representative", "supervisor", "live agent", "real person", "transfer me", "speak to someone"),
    ),
    (
        EscalationReason.MEDICAL_OR_CLINICAL_REQUEST,
        ("diagnosis", "lab result", "clinical", "medical advice", "doctor", "physician"),
    ),
    (
        EscalationReason.BILLING_DISPUTE,
        ("dispute", "wrong charge", "incorrect bill", "overcharged", "fraud"),
    ),
    (
        EscalationReason.CUSTOMER_FRUSTRATION,
        ("this is ridiculous", "this is unacceptable", "i'm very upset", "i am upset", "i am angry", "terrible service"),
    ),
    (
        EscalationReason.PAYMENT_NEGOTIATION,
        ("payment plan", "settle", "negotiate", "write off", "waive the balance"),
    ),
]


class EscalationPolicy:
    """Deterministic escalation trigger detection for the billing agent."""

    def evaluate_turn(
        self,
        call_state: Dict[str, Any],
        user_text: str,
        agent_response: Optional[str] = None,
    ) -> EscalationDecision:
        text = user_text.lower()

        # Check phrase triggers in priority order
        for reason, phrases in _TRIGGER_MAP:
            if any(phrase in text for phrase in phrases):
                caller_msg = _CALLER_MESSAGES.get(reason, "I will connect you with a human agent.")
                return EscalationDecision(
                    should_escalate=True,
                    reason=reason,
                    priority="high" if reason == EscalationReason.CALLER_REQUESTED_HUMAN else "medium",
                    caller_message=caller_msg,
                    internal_note=f"Trigger phrase matched for {reason.value}",
                    recommended_destination="billing_queue",
                    safe_to_continue_with_ai=False,
                )

        # Identity verification failure (tracked in call state)
        id_failures = call_state.get("identity_verification_failures", 0)
        if id_failures >= 2:
            return EscalationDecision(
                should_escalate=True,
                reason=EscalationReason.FAILED_IDENTITY_VERIFICATION,
                priority="high",
                caller_message=_CALLER_MESSAGES[EscalationReason.FAILED_IDENTITY_VERIFICATION],
                internal_note="Identity verification failed 2+ times",
                recommended_destination="billing_queue",
                safe_to_continue_with_ai=False,
            )

        return EscalationDecision(should_escalate=False, safe_to_continue_with_ai=True)


_CALLER_MESSAGES: Dict[EscalationReason, str] = {
    EscalationReason.CALLER_REQUESTED_HUMAN: (
        "Of course. Let me connect you with a human billing specialist right away."
    ),
    EscalationReason.FAILED_IDENTITY_VERIFICATION: (
        "I'm sorry, I'm unable to verify your identity. "
        "I'll transfer you to a billing agent who can assist further."
    ),
    EscalationReason.BILLING_DISPUTE: (
        "I understand you'd like to dispute this charge. "
        "Let me connect you with a specialist who can review this with you."
    ),
    EscalationReason.CUSTOMER_FRUSTRATION: (
        "I'm sorry for the difficulty. Let me get a human agent to help you immediately."
    ),
    EscalationReason.MEDICAL_OR_CLINICAL_REQUEST: (
        "I'm only able to assist with billing questions. "
        "Let me transfer you to the appropriate department."
    ),
    EscalationReason.PAYMENT_NEGOTIATION: (
        "Payment arrangements need to be handled by our billing team. "
        "Let me connect you with a specialist."
    ),
}


class HandoffSummaryBuilder:
    """Build a structured handoff summary from a call context."""

    def build(
        self,
        call_session_id: str,
        messages: List[Dict[str, str]],
        billing_context: Optional[Dict[str, Any]],
        escalation_reason: str,
        last_agent_message: str = "",
    ) -> HandoffSummary:
        billing = billing_context or {}
        # Summarise conversation from last 6 messages — no PHI in details field
        turn_count = len([m for m in messages if m.get("role") == "user"])
        summary = (
            f"Call escalated after {turn_count} turns. "
            f"Reason: {escalation_reason}. "
            f"Claim: {billing.get('claim_number', 'N/A')} | "
            f"Denial: {billing.get('denial_code', 'N/A')}."
        )
        return HandoffSummary(
            call_session_id=call_session_id,
            claim_number=billing.get("claim_number"),
            payer_name=billing.get("payer_name"),
            patient_name=billing.get("patient_name"),
            escalation_reason=escalation_reason,
            priority="high",
            conversation_summary=summary,
            last_agent_message=last_agent_message,
        )
