"""Chat ke data models."""
from dataclasses import dataclass, field
from typing import Literal

Role = Literal["system", "user", "assistant"]


@dataclass
class Message:
    role: Role
    content: str

    def to_api(self) -> dict:
        return {"role": self.role, "content": self.content}


@dataclass
class Conversation:
    customer_phone: str
    system_prompt: str
    messages: list[Message] = field(default_factory=list)
    max_history: int = 10

    def add(self, role: Role, content: str) -> None:
        self.messages.append(Message(role, content))
        self.messages = self.messages[-self.max_history:]     # purane messages kaat do

    def to_api_format(self) -> list[dict]:
        return [{"role": "system", "content": self.system_prompt}] + [m.to_api() for m in self.messages]
