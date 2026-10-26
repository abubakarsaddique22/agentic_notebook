"""Authorization and business rules, as plain functions.

Kept separate from the tool wrappers so they are easy to unit-test and reuse
(M8.4 builds on these). The LLM never decides these questions; code does.
"""
from dataclasses import dataclass
from typing import Literal

# Strings that must never appear in any output (DLP denylist).
# M8.6 removes the first one from the prompt entirely; until then output validation guards it.
PROTECTED_STRINGS = ["MGR-OVERRIDE-2026", "STAFF-90-OFF"]

REFUND_AUTO_APPROVE_LIMIT_PKR = 5000
PII_FIELDS = ("customer_name", "email", "phone", "address")


def can_access_order(order: dict | None, customer_id: str) -> bool:
    """Object-level authorization: you may only touch your own orders (fixes BOLA, V2)."""
    return bool(order) and order.get("customer_id") == customer_id


@dataclass(frozen=True)
class RefundDecision:
    action: Literal["deny", "execute", "needs_approval"]
    reason: str


def decide_refund(order: dict | None, amount_pkr, customer_id: str) -> RefundDecision:
    if not can_access_order(order, customer_id):
        # Same message as "does not exist", so attackers can't probe which order IDs are real.
        return RefundDecision("deny", "No such order on your account.")
    try:
        amount = int(amount_pkr)
    except (TypeError, ValueError):
        return RefundDecision("deny", "Refund amount must be a whole number in PKR.")
    if amount <= 0:
        return RefundDecision("deny", "Refund amount must be positive.")
    if amount > order["total_pkr"]:
        return RefundDecision("deny", f"Refund cannot exceed the PKR {order['total_pkr']} paid for this order.")
    if order.get("status") != "delivered":
        return RefundDecision("deny", "Refunds are only possible for delivered orders.")
    if amount > REFUND_AUTO_APPROVE_LIMIT_PKR:
        return RefundDecision("needs_approval", "Refunds above PKR 5,000 need a store manager's approval.")
    return RefundDecision("execute", "Within policy.")


def foreign_private_values(orders: dict, customer_id: str) -> list[str]:
    """PII belonging to every customer EXCEPT the logged-in one (must never be shown to them)."""
    values: set[str] = set()
    for order in orders.values():
        if order.get("customer_id") != customer_id:
            values.update(str(order[f]) for f in PII_FIELDS if order.get(f))
    return sorted(values)
