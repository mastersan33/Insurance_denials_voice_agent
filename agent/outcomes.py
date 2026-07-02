"""Call outcome taxonomy for the outbound billing voice agent.

Used by media_stream.py, call_session_service, and the Day 13 test matrix.
Replacing raw strings with this enum prevents typos and makes outcome
tracking auditable.
"""
from enum import Enum
from typing import Dict


class CallOutcome(str, Enum):
    COMPLETED = "completed"
    RESOLVED = "resolved"
    FOLLOW_UP_REQUIRED = "follow_up_required"
    TRANSFERRED_TO_HUMAN = "transferred_to_human"
    NO_ANSWER = "no_answer"
    VOICEMAIL = "voicemail"
    FAILED = "failed"
    WRONG_NUMBER = "wrong_number"
    IDENTITY_VERIFICATION_FAILED = "identity_verification_failed"
    CALLBACK_REQUESTED = "callback_requested"
    INCOMPLETE = "incomplete"


OUTCOME_DESCRIPTIONS: Dict[CallOutcome, str] = {
    CallOutcome.COMPLETED: "The call completed normally.",
    CallOutcome.RESOLVED: "The billing issue was fully handled during the call.",
    CallOutcome.FOLLOW_UP_REQUIRED: "The case needs a future billing follow-up.",
    CallOutcome.TRANSFERRED_TO_HUMAN: "The caller was escalated to a human billing agent.",
    CallOutcome.NO_ANSWER: "The outbound call was not answered.",
    CallOutcome.VOICEMAIL: "The call reached voicemail.",
    CallOutcome.FAILED: "The call failed before completion.",
    CallOutcome.WRONG_NUMBER: "The reached party indicated this was the wrong number.",
    CallOutcome.IDENTITY_VERIFICATION_FAILED: "The caller's identity could not be verified.",
    CallOutcome.CALLBACK_REQUESTED: "The caller requested a callback at another time.",
    CallOutcome.INCOMPLETE: "The call ended before the billing workflow was completed.",
}
