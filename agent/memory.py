from dataclasses import dataclass, field


@dataclass
class ConversationMemoryManager:
    """Manages conversation history with sliding window for token management."""

    max_messages: int = 20
    messages: list[dict] = field(default_factory=list)

    def add_message(self, role: str, content: str) -> None:
        self.messages.append({"role": role, "content": content})
        if len(self.messages) > self.max_messages:
            # Keep system message + last N messages
            system_msgs = [m for m in self.messages if m["role"] == "system"]
            other_msgs = [m for m in self.messages if m["role"] != "system"]
            self.messages = system_msgs + other_msgs[-(self.max_messages - len(system_msgs)):]

    def get_messages(self) -> list[dict]:
        return self.messages.copy()

    def get_summary(self) -> str:
        """Generate a summary of the conversation for checkpointing."""
        turns = []
        for msg in self.messages:
            if msg["role"] in ("user", "assistant"):
                speaker = "Rep" if msg["role"] == "user" else "Agent"
                turns.append(f"{speaker}: {msg['content'][:100]}")
        return "\n".join(turns[-10:])

    def clear(self) -> None:
        self.messages.clear()
