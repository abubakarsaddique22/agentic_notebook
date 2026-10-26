"""Secure versions of the four tools (layered defence, M8.2).

What changed vs app/tools.py:
  - Identity comes from ToolRuntime context (set by code), not from model arguments.
    The model literally cannot ask for another customer's data or pick an email recipient.
  - get_order: ownership check (least privilege / authorization).
  - send_email: recipient is fixed to the logged-in customer (restricted tool) and the body
    passes output validation (no secrets, no other customers' PII, no exfil links).
  - issue_refund: ownership + amount + status checks; large refunds become a pending
    request instead of executing (a simple confirmation gate; M8.4 adds real human approval).
  - search_knowledge_base: every passage is fenced as untrusted data, and passages that
    look like injections are quarantined and logged instead of reaching the model.
"""
import json

from langchain.tools import ToolRuntime, tool

from app.config import OUTPUT_DIR
from app.knowledge_base import search
from app.session import UserContext
from app.tools import OUTBOX_FILE, REFUNDS_FILE, _append_jsonl, _load_orders
from m8_2_prompt_injection.defenses import detect_injection, fence_untrusted, validate_output
from m8_2_prompt_injection.policies import (
    PROTECTED_STRINGS,
    can_access_order,
    decide_refund,
    foreign_private_values,
)

REFUND_REQUESTS_FILE = OUTPUT_DIR / "refund_requests.jsonl"
QUARANTINE_FILE = OUTPUT_DIR / "quarantine.jsonl"


@tool
def search_knowledge_base(query: str) -> str:
    """Search TimeHouse store policies (shipping, returns, refunds, warranty) and return relevant passages."""
    blocks = []
    for doc in search(query, k=3):
        source = doc.metadata.get("source", "unknown")
        hits = detect_injection(doc.page_content)
        if hits:
            _append_jsonl(QUARANTINE_FILE, {"source": source, "patterns": hits, "query": query})
            blocks.append(fence_untrusted("[Passage withheld: it contained instructions aimed at the assistant.]", source))
            continue
        blocks.append(fence_untrusted(doc.page_content, source))
    return "\n\n".join(blocks) if blocks else "No relevant policy found."


@tool
def get_order(order_id: str, runtime: ToolRuntime[UserContext]) -> str:
    """Look up one of the logged-in customer's own orders by its ID (for example ORD-1001)."""
    user = runtime.context
    order = _load_orders().get(order_id.strip().upper())
    if not can_access_order(order, user.customer_id):
        return f"No order {order_id} found on your account."
    return fence_untrusted(json.dumps(order, ensure_ascii=False), "orders_db")


@tool
def send_email(subject: str, body: str, runtime: ToolRuntime[UserContext]) -> str:
    """Email the logged-in customer (only them) a copy of information about their own orders."""
    user = runtime.context
    check = validate_output(
        f"{subject}\n{body}",
        protected_strings=PROTECTED_STRINGS,
        private_values=foreign_private_values(_load_orders(), user.customer_id),
    )
    if check.blocked:
        return "Email not sent: the content was blocked by the store's data protection policy."
    _append_jsonl(OUTBOX_FILE, {"to": user.email, "subject": subject, "body": check.text})
    return f"Email sent to the customer's registered address ({user.email})."


@tool
def issue_refund(order_id: str, amount_pkr: int, runtime: ToolRuntime[UserContext]) -> str:
    """Refund the logged-in customer for one of their own delivered orders, in PKR."""
    user = runtime.context
    oid = order_id.strip().upper()
    decision = decide_refund(_load_orders().get(oid), amount_pkr, user.customer_id)
    if decision.action == "deny":
        return f"Refund not possible: {decision.reason}"
    if decision.action == "needs_approval":
        _append_jsonl(REFUND_REQUESTS_FILE, {"order_id": oid, "amount_pkr": int(amount_pkr), "customer_id": user.customer_id})
        return f"Refund request for PKR {amount_pkr} on {oid} sent to a store manager for approval."
    _append_jsonl(REFUNDS_FILE, {"order_id": oid, "amount_pkr": int(amount_pkr), "customer_id": user.customer_id})
    return f"Refund of PKR {amount_pkr} issued for {oid}."


SECURE_TOOLS = [search_knowledge_base, get_order, send_email, issue_refund]
