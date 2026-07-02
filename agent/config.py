from dataclasses import dataclass

from backend.app.config.settings import settings


@dataclass
class AgentConfig:
    """Configuration for the voice agent."""

    model: str = settings.openai_model
    temperature: float = 0.3
    max_tokens: int = 200
    max_phase_turns: int = 15
    confidence_threshold: float = 0.6
    max_ivr_attempts: int = 10
    max_call_duration_seconds: int = 1800

    # Phase transition thresholds
    ivr_max_turns: int = 20
    auth_max_turns: int = 10
    gathering_max_turns: int = 30
    negotiation_max_turns: int = 20
    wrap_up_max_turns: int = 10


agent_config = AgentConfig()
