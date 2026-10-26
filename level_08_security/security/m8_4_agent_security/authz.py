"""Authorization and safe tool wrappers (the real fix for S1/S2/S6).

Key idea from the roadmap: the LLM's tool choice is a PROPOSAL. Consequences
are decided by ordinary code that the model cannot argue with. So we:

  - pass the real session (who is logged in) from OUTSIDE the model, not the prompt
  - check ownership in code before returning any order         (fixes V2 / S1 BOLA)
  - cap refund amounts and require approval for big/irreversible ones (V4 / S2)
  - separate read-only tools from consequential ones
  - enforce an email recipient allow-list                      (V3 / S6)

These wrappers take a Session object, so the same raw data layer serves every
customer safely.
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from langchain_core.tools import tool

from app.config import DATA_DIR, OUTPUT_DIR
from app.tools import _append_jsonl, OUTBOX_FILE, REFUNDS_FILE

ORDERS_FILE = DATA_DIR / "orders.json"

REFUND_AUTO_LIMIT_PKR = 5000   # above this -> human approval required
APPROVAL_QUEUE = OUTPUT_DIR / "approval_queue.jsonl"


@dataclass(frozen=True)
class Session:
    customer_id: str
    name: str
    email: str


def _load_orders() -> dict:
    return json.loads(ORDERS_FILE.read_text(encoding="utf-8"))


class ToolDenied(Exception):
    """Raised when an action is not allowed. Caller turns it into a safe message."""


# ---------------- read-only tool (with ownership check) ----------------

def owns_order(session: Session, order: dict) -> bool:
    return order.get("customer_id") == session.customer_id


def lookup_order(session: Session, order_id: str) -> dict:
    """Return an order ONLY if it belongs to the session's customer."""
    order = _load_orders().get(order_id.strip().upper())
    if not order:
        raise ToolDenied(f"No order found with id {order_id}.")
    if not owns_order(session, order):
        # Do not reveal that the order exists for someone else.
        raise ToolDenied(f"No order found with id {order_id}.")
    return order


# ---------------- consequential tools ----------------

def guarded_send_email(session: Session, to: str, subject: str, body: str) -> str:
    if to.strip().lower() != session.email.lower():
        raise ToolDenied(
            f"Email can only go to your own registered address ({session.email})."
        )
    _append_jsonl(OUTBOX_FILE, {"to": to, "subject": subject, "body": body})
    return f"Email sent to {to}."


def guarded_issue_refund(session: Session, order_id: str, amount_pkr: int) -> str:
    order = lookup_order(session, order_id)  # ownership enforced here, reuses the check
    paid = int(order["total_pkr"])
    if amount_pkr <= 0:
        raise ToolDenied("Refund amount must be positive.")
    if amount_pkr > paid:
        raise ToolDenied(f"Refund cannot exceed what was paid (PKR {paid}).")
    if amount_pkr > REFUND_AUTO_LIMIT_PKR:
        # Irreversible + large -> queue for a human instead of doing it (M8.4 approval gate)
        _append_jsonl(APPROVAL_QUEUE, {
            "type": "refund", "order_id": order_id, "amount_pkr": amount_pkr,
            "customer_id": session.customer_id, "status": "pending_human_approval",
        })
        return (
            f"Your refund of PKR {amount_pkr} needs manager approval and has been "
            f"queued. A human will review it shortly."
        )
    _append_jsonl(REFUNDS_FILE, {"order_id": order_id, "amount_pkr": amount_pkr})
    return f"Refund of PKR {amount_pkr} issued for {order_id}."


# ---------------- build session-bound LangChain tools ----------------

def make_tools(session: Session, search_tool) -> list:
    """Bind the session into closures so the model never handles identity itself.

    search_tool is passed in (the fenced + audience-filtered one from M8.3/M8.5),
    so this module stays focused on authorization.
    """

    @tool
    def get_order(order_id: str) -> str:
        """Look up ONE of your own orders by its ID (e.g. ORD-1001)."""
        try:
            return json.dumps(lookup_order(session, order_id), ensure_ascii=False)
        except ToolDenied as e:
            return str(e)

    @tool
    def send_email(to: str, subject: str, body: str) -> str:
        """Email a copy of information to your own registered email address."""
        try:
            return guarded_send_email(session, to, subject, body)
        except ToolDenied as e:
            return f"BLOCKED: {e}"

    @tool
    def issue_refund(order_id: str, amount_pkr: int) -> str:
        """Request a refund on one of your own orders."""
        try:
            return guarded_issue_refund(session, order_id, amount_pkr)
        except ToolDenied as e:
            return f"BLOCKED: {e}"

    return [search_tool, get_order, send_email, issue_refund]
