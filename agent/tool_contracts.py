"""Typed Pydantic contracts for all billing agent tools.

Day 2 requirement: every tool must have typed inputs, typed outputs, and a docstring.
Using Pydantic models as args_schema enforces this at runtime and makes tool signatures
self-documenting in the OpenAI function-calling spec.
"""
from typing import List, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Claim lookup
# ---------------------------------------------------------------------------

class LookupClaimInput(BaseModel):
    claim_number: str = Field(..., description="The insurance claim number.")
    payer_name: str = Field(..., description="The name of the insurance payer.")


class ClaimLookupOutput(BaseModel):
    found: bool
    claim_number: str
    payer_name: str
    status: Optional[str] = None
    denial_code: Optional[str] = None
    denial_reason: Optional[str] = None
    amount_billed: Optional[float] = None
    date_of_service: Optional[str] = None
    next_step: Optional[str] = None
    source: str = "billing_db"


# ---------------------------------------------------------------------------
# Gathered information update
# ---------------------------------------------------------------------------

class UpdateGatheredInfoInput(BaseModel):
    field: str = Field(
        ...,
        description=(
            "Field to update. Allowed: denial_reason, appeal_deadline, appeal_method, "
            "reference_number, representative_name, resolution_offered."
        ),
    )
    value: str = Field(..., description="The value to store for the field.")


class UpdateGatheredInfoOutput(BaseModel):
    field: str
    value: str
    updated: bool


# ---------------------------------------------------------------------------
# Call event logging
# ---------------------------------------------------------------------------

class LogCallEventInput(BaseModel):
    event_type: str = Field(
        ...,
        description="Type of event (e.g., phase_change, info_gathered, error, tool_failure).",
    )
    description: str = Field(..., description="Human-readable description of the event.")


class LogCallEventOutput(BaseModel):
    event_type: str
    description: str
    logged: bool


# ---------------------------------------------------------------------------
# Knowledge base search
# ---------------------------------------------------------------------------

class SearchKnowledgeBaseInput(BaseModel):
    query: str = Field(..., description="Search query about billing policies or procedures.")
    category: str = Field(
        "general",
        description="Category filter: denial_codes | appeal_procedures | coverage_policies | general.",
    )


class SearchKnowledgeBaseOutput(BaseModel):
    query: str
    category: str
    result: str
    found: bool


# ---------------------------------------------------------------------------
# Follow-up date
# ---------------------------------------------------------------------------

class SetFollowupDateInput(BaseModel):
    case_id: str = Field(..., description="Billing case identifier.")
    followup_date: str = Field(..., description="Follow-up date in YYYY-MM-DD format.")
    reason: str = Field(..., description="Reason a follow-up is needed.")


class SetFollowupDateOutput(BaseModel):
    case_id: str
    followup_date: str
    reason: str
    scheduled: bool


# ---------------------------------------------------------------------------
# Member eligibility
# ---------------------------------------------------------------------------

class VerifyMemberEligibilityInput(BaseModel):
    payer_name: str = Field(..., description="Insurance payer name.")
    member_id: str = Field(..., description="Member or subscriber ID.")
    date_of_service: str = Field(..., description="Date of service in YYYY-MM-DD format.")


class MemberEligibilityOutput(BaseModel):
    payer_name: str
    member_id: str
    date_of_service: str
    eligible: bool
    coverage_status: Optional[str] = None
    copay: Optional[str] = None
    deductible_met: Optional[bool] = None
    notes: Optional[str] = None


# ---------------------------------------------------------------------------
# Patient balance
# ---------------------------------------------------------------------------

class GetPatientBalanceInput(BaseModel):
    case_id: str = Field(..., description="Billing case identifier.")


class PatientBalanceOutput(BaseModel):
    case_id: str
    balance_due: Optional[str] = None
    last_payment_date: Optional[str] = None
    found: bool
    source: str = "billing_db"


# ---------------------------------------------------------------------------
# Human handoff
# ---------------------------------------------------------------------------

class HumanHandoffInput(BaseModel):
    reason: str = Field(..., description="Why the call is being escalated to a human agent.")


class HumanHandoffOutput(BaseModel):
    reason: str
    requested: bool
    queue: str = "billing_escalation_queue"


# ---------------------------------------------------------------------------
# End call
# ---------------------------------------------------------------------------

class EndCallInput(BaseModel):
    summary: str = Field(..., description="Brief summary of the call outcome.")
    outcome: str = Field(
        ...,
        description=(
            "Final call outcome. One of: resolved, follow_up_required, transferred_to_human, "
            "no_answer, voicemail, failed, wrong_number, identity_verification_failed, "
            "callback_requested, incomplete."
        ),
    )


class EndCallOutput(BaseModel):
    summary: str
    outcome: str
    ended: bool
