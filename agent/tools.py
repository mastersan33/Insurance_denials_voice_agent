from langchain_core.tools import tool


@tool
def lookup_claim(claim_number: str, payer_name: str) -> str:
    """Look up claim details from the billing system.

    Args:
        claim_number: The insurance claim number
        payer_name: The insurance payer name
    """
    return f"Claim {claim_number} with {payer_name}: Status=Denied, Amount=$1,500.00"


@tool
def update_gathered_info(field: str, value: str) -> str:
    """Update gathered information from the call.

    Args:
        field: The field name (e.g., 'denial_reason', 'appeal_deadline', 'reference_number')
        value: The value to store
    """
    return f"Updated {field} = {value}"


@tool
def log_call_event(event_type: str, description: str) -> str:
    """Log a significant event during the call.

    Args:
        event_type: Type of event (e.g., 'phase_change', 'info_gathered', 'error')
        description: Description of the event
    """
    return f"Logged: [{event_type}] {description}"


@tool
def search_knowledge_base(query: str, category: str = "general") -> str:
    """Search the knowledge base for insurance policies and procedures.

    Args:
        query: The search query
        category: Category filter (denial_codes, appeal_procedures, coverage_policies)
    """
    return f"Knowledge base result for '{query}': Standard appeal deadline is 180 days from denial date."


@tool
def request_human_handoff(reason: str) -> str:
    """Request transfer to a human agent when the AI cannot handle the situation.

    Args:
        reason: Why handoff is needed
    """
    return f"Human handoff requested: {reason}"


@tool
def end_call(summary: str) -> str:
    """End the current call with a summary.

    Args:
        summary: Brief summary of call outcome
    """
    return f"Call ending. Summary: {summary}"


AGENT_TOOLS = [
    lookup_claim,
    update_gathered_info,
    log_call_event,
    search_knowledge_base,
    request_human_handoff,
    end_call,
]
