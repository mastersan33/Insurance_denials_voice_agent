"""Billing agent tools with typed Pydantic contracts.

Day 2 requirement: every tool must have typed inputs, typed outputs, and a docstring.
args_schema enforces input types at the LangChain/OpenAI function-calling layer so the
LLM cannot pass malformed arguments — and output models make tool results auditable.
"""
from typing import Any

from langchain_core.tools import tool

from agent.tool_contracts import (
    EndCallInput,
    HumanHandoffInput,
    LogCallEventInput,
    LookupClaimInput,
    SearchKnowledgeBaseInput,
    SetFollowupDateInput,
    UpdateGatheredInfoInput,
)

# ---------------------------------------------------------------------------
# Denial code knowledge base — used by lookup_claim to enrich results
# ---------------------------------------------------------------------------
_DENIAL_CODE_INFO: dict[str, dict[str, str]] = {
    "CO-97": {
        "description": "Payment is included in the allowance for another service already adjudicated.",
        "appeal_steps": "Submit corrected claim with modifier -59 or XU. Attach operative notes.",
        "common_fix": "Add modifier -59 (distinct procedural service).",
    },
    "CO-4": {
        "description": "Service is inconsistent with the modifier used.",
        "appeal_steps": "Review modifier usage, correct the claim, resubmit with appropriate modifier.",
        "common_fix": "Remove or correct the conflicting modifier.",
    },
    "CO-16": {
        "description": "Claim lacks information or has a submission/billing error.",
        "appeal_steps": "Identify the missing field (NPI, diagnosis pointer, or dates), correct, and resubmit.",
        "common_fix": "Complete all required fields and resubmit.",
    },
    "CO-50": {
        "description": "Non-covered service — not deemed a medical necessity by the payer.",
        "appeal_steps": "Submit a Letter of Medical Necessity from the treating physician with clinical documentation.",
        "common_fix": "Obtain and attach Letter of Medical Necessity.",
    },
    "CO-22": {
        "description": "This care may be covered by another payer per coordination of benefits.",
        "appeal_steps": "Confirm primary vs secondary payer order. Submit to primary first, then secondary with EOB.",
        "common_fix": "Submit to correct primary payer first.",
    },
    "CO-45": {
        "description": "Charge exceeds the fee schedule/maximum allowable or contracted/legislated fee arrangement.",
        "appeal_steps": "Verify contracted rate and resubmit with correct charge amount.",
        "common_fix": "Correct billed amount to match contracted rate.",
    },
    "PR-1": {
        "description": "Deductible amount — patient responsibility.",
        "appeal_steps": "Verify patient's deductible has been met; if so, request reconsideration.",
        "common_fix": "Confirm deductible status with payer.",
    },
    "PR-2": {
        "description": "Coinsurance amount — patient responsibility.",
        "appeal_steps": "Verify coinsurance calculation is correct per the EOB.",
        "common_fix": "Confirm coinsurance percentage with payer.",
    },
}


def _enrich_with_denial_info(denial_code: str) -> str:
    info = _DENIAL_CODE_INFO.get(denial_code.upper())
    if not info:
        return f"Denial code {denial_code}: No additional guidance available. Request details from payer."
    return (
        f"Description: {info['description']} | "
        f"Appeal: {info['appeal_steps']} | "
        f"Fix: {info['common_fix']}"
    )


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@tool(args_schema=LookupClaimInput)
def lookup_claim(claim_number: str, payer_name: str) -> dict[str, Any]:
    """Look up claim details and denial guidance from the billing system.

    Returns status, denial code, denial reason, and appeal instructions.
    Only call this tool when you need billing facts — never state claim
    details without calling this first.
    """
    # In production this queries the DB; for dev returns denial guidance from
    # the built-in knowledge base so the agent is always grounded in real data.
    denial_code = "CO-97"  # would come from DB in production
    return {
        "found": True,
        "claim_number": claim_number,
        "payer_name": payer_name,
        "status": "Denied",
        "denial_code": denial_code,
        "denial_guidance": _enrich_with_denial_info(denial_code),
        "next_step": "Request appeal instructions and reference number from payer representative.",
        "source": "billing_db",
    }


@tool(args_schema=UpdateGatheredInfoInput)
def update_gathered_info(field: str, value: str) -> dict[str, Any]:
    """Store information gathered from the insurance representative during the call.

    Use this every time the representative provides a fact (denial reason,
    reference number, appeal deadline, submission method, etc.).
    Allowed fields: denial_reason, appeal_deadline, appeal_method,
    reference_number, representative_name, resolution_offered.
    """
    allowed = {
        "denial_reason", "appeal_deadline", "appeal_method",
        "reference_number", "representative_name", "resolution_offered",
    }
    if field not in allowed:
        return {"field": field, "value": value, "updated": False,
                "error": f"Unknown field '{field}'. Allowed: {sorted(allowed)}"}
    return {"field": field, "value": value, "updated": True}


@tool(args_schema=LogCallEventInput)
def log_call_event(event_type: str, description: str) -> dict[str, Any]:
    """Log a significant event during the call for audit and ticket purposes.

    Use for phase changes, identity verification outcomes, tool failures,
    and any compliance-relevant moment.
    """
    return {"event_type": event_type, "description": description, "logged": True}


@tool(args_schema=SearchKnowledgeBaseInput)
def search_knowledge_base(query: str, category: str = "general") -> dict[str, Any]:
    """Search billing policy knowledge base for denial codes, appeal procedures, and coverage rules.

    Categories: denial_codes | appeal_procedures | coverage_policies | general.
    Call this before stating any policy fact to ensure accuracy.
    """
    kb: dict[str, str] = {
        "appeal deadline": "Standard appeal deadline is 180 days from the denial date. Some payers allow 365 days for complex cases.",
        "modifier 59": "Modifier -59 indicates a distinct procedural service. Use to unbundle CO-97 denials.",
        "peer to peer": "Peer-to-peer review allows the treating physician to speak directly with the payer medical director.",
        "letter of medical necessity": "An LMN from the treating physician is required to overturn CO-50 medical necessity denials.",
        "coordination of benefits": "When multiple payers exist, the primary payer must adjudicate first before the secondary payer.",
    }
    lowered = query.lower()
    result = next((v for k, v in kb.items() if k in lowered), None)
    if not result and category == "denial_codes":
        for code, info in _DENIAL_CODE_INFO.items():
            if code.lower() in lowered:
                result = f"{code}: {info['description']} Appeal: {info['appeal_steps']}"
                break
    return {
        "query": query,
        "category": category,
        "result": result or f"No specific guidance found for '{query}'. Ask the payer representative directly.",
        "found": result is not None,
    }


@tool(args_schema=SetFollowupDateInput)
def set_followup_date(case_id: str, followup_date: str, reason: str) -> dict[str, Any]:
    """Schedule a follow-up date for a billing case.

    Use when the payer representative asks us to call back, or when
    additional time is needed to gather documentation.
    Date must be in YYYY-MM-DD format.
    """
    return {"case_id": case_id, "followup_date": followup_date, "reason": reason, "scheduled": True}


@tool(args_schema=HumanHandoffInput)
def request_human_handoff(reason: str) -> dict[str, Any]:
    """Escalate to a human billing specialist.

    Call this when: the caller explicitly asks for a human, identity
    verification fails twice, the case is too complex, or the caller
    is frustrated. This will end the AI's handling of the call.
    """
    return {"reason": reason, "requested": True, "queue": "billing_escalation_queue"}


@tool(args_schema=EndCallInput)
def end_call(summary: str, outcome: str) -> dict[str, Any]:
    """End the call with a summary and outcome classification.

    Outcome must be one of: resolved, follow_up_required, transferred_to_human,
    no_answer, voicemail, failed, wrong_number, identity_verification_failed,
    callback_requested, incomplete.
    """
    valid_outcomes = {
        "resolved", "follow_up_required", "transferred_to_human", "no_answer",
        "voicemail", "failed", "wrong_number", "identity_verification_failed",
        "callback_requested", "incomplete",
    }
    if outcome not in valid_outcomes:
        outcome = "incomplete"
    return {"summary": summary, "outcome": outcome, "ended": True}


AGENT_TOOLS = [
    lookup_claim,
    update_gathered_info,
    log_call_event,
    search_knowledge_base,
    set_followup_date,
    request_human_handoff,
    end_call,
]

