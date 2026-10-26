"""Who is logged in.

In a real app this comes from your auth system (JWT, session cookie, WhatsApp
number lookup). The key security rule: identity is passed to tools by CODE
through the agent's runtime context, never typed by the model as a tool argument.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class UserContext:
    customer_id: str
    name: str
    email: str


DEFAULT_USER = UserContext(customer_id="cust_001", name="Ali Raza", email="ali.raza@example.com")
