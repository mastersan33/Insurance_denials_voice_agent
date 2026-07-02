from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode

from agent.config import agent_config
from agent.prompts import build_phase_prompt, build_system_prompt
from agent.state import AgentState
from agent.tools import AGENT_TOOLS

from backend.app.config.settings import settings


def create_llm() -> ChatOpenAI:
    return ChatOpenAI(
        model=agent_config.model,
        temperature=agent_config.temperature,
        max_tokens=agent_config.max_tokens,
        api_key=settings.openai_api_key,
        streaming=True,
    )


async def planner_node(state: AgentState) -> dict:
    """Assess state and decide next action."""
    phase = state.get("current_phase", "ivr_navigation")
    turn_count = state.get("phase_turn_count", 0)
    confidence = state.get("confidence_score", 1.0)

    # Check escalation triggers
    if confidence < agent_config.confidence_threshold:
        return {
            "should_escalate": True,
            "escalation_reason": "Low confidence score",
        }

    # Check phase timeouts
    max_turns = {
        "ivr_navigation": agent_config.ivr_max_turns,
        "authentication": agent_config.auth_max_turns,
        "information_gathering": agent_config.gathering_max_turns,
        "negotiation": agent_config.negotiation_max_turns,
        "wrap_up": agent_config.wrap_up_max_turns,
    }

    if turn_count > max_turns.get(phase, 15):
        return {
            "should_escalate": True,
            "escalation_reason": f"Phase '{phase}' exceeded maximum turns",
        }

    return {"phase_turn_count": turn_count + 1}


async def executor_node(state: AgentState) -> dict:
    """Generate AI response using LLM with tools."""
    llm = create_llm()
    llm_with_tools = llm.bind_tools(AGENT_TOOLS)

    phase = state.get("current_phase", "ivr_navigation")
    system_prompt = build_system_prompt(state)
    phase_prompt = build_phase_prompt(phase, state)

    messages = state.get("messages", [])
    full_messages = [
        {"role": "system", "content": system_prompt + "\n\n" + phase_prompt},
        *messages,
    ]

    response = await llm_with_tools.ainvoke(full_messages)

    return {"messages": [response], "response_text": response.content or ""}


async def observer_node(state: AgentState) -> dict:
    """Evaluate conversation progress and detect phase transitions."""
    response_text = state.get("response_text", "")
    phase = state.get("current_phase", "ivr_navigation")

    # Detect human on IVR
    if phase == "ivr_navigation" and "HUMAN_DETECTED" in response_text:
        return {
            "current_phase": "authentication",
            "phase_turn_count": 0,
            "human_detected": True,
        }

    # Detect DTMF request
    if response_text.startswith("DTMF:"):
        digit = response_text.replace("DTMF:", "").strip()
        return {"dtmf_to_send": digit}

    # Check if we should end
    if state.get("should_end_call", False):
        return {"should_end_call": True}

    return {}


def should_continue(state: AgentState) -> str:
    """Route after executor - check if tools were called."""
    messages = state.get("messages", [])
    if messages and hasattr(messages[-1], "tool_calls") and messages[-1].tool_calls:
        return "tools"
    return "observer"


def should_end(state: AgentState) -> str:
    """Route after observer - check if call should end or escalate."""
    if state.get("should_escalate", False):
        return "end"
    if state.get("should_end_call", False):
        return "end"
    return "planner"


def build_agent_graph() -> StateGraph:
    """Build the LangGraph state machine for the voice agent."""
    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("planner", planner_node)
    graph.add_node("executor", executor_node)
    graph.add_node("observer", observer_node)
    graph.add_node("tools", ToolNode(AGENT_TOOLS))

    # Define edges
    graph.add_edge(START, "planner")
    graph.add_edge("planner", "executor")
    graph.add_conditional_edges("executor", should_continue, {"tools": "tools", "observer": "observer"})
    graph.add_edge("tools", "executor")
    graph.add_conditional_edges("observer", should_end, {"planner": "planner", "end": END})

    return graph.compile()


# Singleton compiled graph
agent_graph = build_agent_graph()
