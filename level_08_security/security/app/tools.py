"""Tools the support agent can call.

This is v0: deliberately written the way many real first versions are,
so we can attack it in later modules. Each weakness is tagged with its ID
from m8_1_threat_model/THREAT_MODEL.md.

Side effects are simulated: emails and refunds are appended to files in
outputs/ instead of really being sent, so attacks are safe to run.
"""
import json
from datetime import datetime, timezone

from langchain_core.tools import tool

from app.config import DATA_DIR, OUTPUT_DIR
from app.knowledge_base import search

ORDERS_FILE = DATA_DIR / "orders.json"
OUTBOX_FILE = OUTPUT_DIR / "outbox.jsonl"
REFUNDS_FILE = OUTPUT_DIR / "refunds.jsonl"


def _load_orders() -> dict:
    return json.loads(ORDERS_FILE.read_text(encoding="utf-8"))


def _append_jsonl(path, record: dict) -> None:
    record["ts"] = datetime.now(timezone.utc).isoformat()
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


@tool
def search_knowledge_base(query: str) -> str:
    """Search TimeHouse store policies (shipping, returns, refunds, warranty) and return relevant passages."""
    docs = search(query, k=3)
    # VULN V6: retrieved text is pasted straight into the model context with no
    # marking that it is untrusted data, so instructions inside a doc look like instructions.
    return "\n\n---\n\n".join(f"[source: {d.metadata['source']}]\n{d.page_content}" for d in docs)


@tool
def get_order(order_id: str) -> str:
    """Look up an order by its ID (for example ORD-1001) and return its details."""
    order = _load_orders().get(order_id.strip().upper())
    if not order:
        return f"No order found with id {order_id}."
    # VULN V2 (BOLA): no check that this order belongs to the logged-in customer.
    # VULN V8: full PII (phone, address, email) is returned to the model.
    return json.dumps(order, ensure_ascii=False)


@tool
def send_email(to: str, subject: str, body: str) -> str:
    """Send an email to the given address."""
    # VULN V3: any recipient and any content. This is the exfiltration path.
    _append_jsonl(OUTBOX_FILE, {"to": to, "subject": subject, "body": body})
    return f"Email sent to {to}."


@tool
def issue_refund(order_id: str, amount_pkr: int) -> str:
    """Issue a refund in PKR for an order."""
    # VULN V4: no ownership check, no amount limit, no human approval.
    _append_jsonl(REFUNDS_FILE, {"order_id": order_id, "amount_pkr": amount_pkr})
    return f"Refund of PKR {amount_pkr} issued for {order_id}."


ALL_TOOLS = [search_knowledge_base, get_order, send_email, issue_refund]
