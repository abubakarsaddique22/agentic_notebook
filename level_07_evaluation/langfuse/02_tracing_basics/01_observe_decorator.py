"""
@observe ke saare important options. Koi LLM call nahi — sirf tracing ka structure.
"""
import time
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from langfuse import get_client, observe  # noqa: E402

langfuse = get_client()


# 1) as_type + custom name
@observe(name="get-order-status", as_type="tool")
def get_order_status(order_id: str) -> dict:
    time.sleep(0.3)  # fake DB call — UI mein latency dikhegi
    return {"order_id": order_id, "status": "shipped"}


# 2) Input capture band — e.g. jab input bohat bara ho ya sensitive ho
@observe(name="load-customer-profile", capture_input=False)
def load_customer_profile(raw_db_row: dict) -> dict:
    return {"name": raw_db_row["name"], "tier": "gold"}


# 3) Runtime par current observation mein info add karna
@observe(name="format-reply")
def format_reply(status: dict, customer: dict) -> str:
    reply = f"{customer['name']} sahab, aap ka order {status['order_id']} {status['status']} ho chuka hai."
    langfuse.update_current_span(
        metadata={"reply_length": len(reply), "template": "order_status_v2"},
        version="2.0",
    )
    return reply


# 4) Parent: andar wale sab iske CHILDREN
@observe(name="handle-customer-message")
def handle_message(message: str, order_id: str) -> str:
    status = get_order_status(order_id)
    customer = load_customer_profile({"name": "Ali", "cnic": "secret", "address": "secret"})
    return format_reply(status, customer)


if __name__ == "__main__":
    print(handle_message("Mera order kahan hai?", "ORD-1001"))
    langfuse.flush()
    print("UI: 'handle-customer-message' trace kholo -> 3 children. 'load-customer-profile' ka input khali hoga.")
