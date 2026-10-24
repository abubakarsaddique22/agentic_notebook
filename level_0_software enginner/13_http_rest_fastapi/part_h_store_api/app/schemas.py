"""Pydantic models: API kya leti hai (In) aur kya deti hai (Out)."""
from typing import Annotated, Literal

from pydantic import BaseModel, Field

OrderStatus = Literal["pending", "shipped", "delivered", "cancelled"]


class OrderOut(BaseModel):
    order_id: str
    status: OrderStatus
    total_pkr: int
    courier: str | None = None


class OrderList(BaseModel):
    items: list[OrderOut]
    total: int
    limit: int
    offset: int


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    message: Annotated[str, Field(min_length=1, max_length=2000)]
    history: Annotated[list[ChatMessage], Field(max_length=20)] = []


class ChatResponse(BaseModel):
    reply: str
    source: Literal["order_lookup", "llm"]
