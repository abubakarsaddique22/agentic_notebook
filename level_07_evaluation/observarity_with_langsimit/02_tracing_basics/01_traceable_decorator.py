"""
@traceable ke saare important options.

Is file mein koi LLM call nahi — sirf tracing ka structure samajhna hai.
"""
import time
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from langsmith import traceable  # noqa: E402
# ---------------------------------------------------------
# traceable  (decorator) -- function ko LangSmith ka "run" (span) bana deta ha
#   Function ka input, output, time, error -- sab trace ma. Andar se doosra
#   @traceable function call ho to wo CHILD run ban jata ha (tree banta ha).
#   Sync, async aur generator -- sab functions pe kaam karta ha.
#   Decorator arguments:
#     name           -> run ka naam (default: function ka naam)
#     run_type       -> "chain" (default) | "llm" | "tool" | "retriever" | "prompt" | "parser"
#                       -- UI isi ke hisaab se run ko dikhata ha (retriever = documents list)
#     tags           -> list of strings, filter karne ke liye
#     metadata       -> dict (version, user_id...), filter + compare ke liye
#     client         -> kaunsa langsmith Client traces bheje (masking / flush ke liye)
#     project_name   -> is function ke runs kis project ma jayen
#     process_inputs / process_outputs -> trace ma jaane se pehle data badlo
#     enabled        -> is function ki tracing on/off
#   Call ke waqt extra: fn(..., langsmith_extra={...})
#     metadata, tags, run_id (apni uuid -- feedback ke liye), project_name,
#     parent, client, name
#   Tracing tabhi hoti ha jab .env ma LANGSMITH_TRACING=true ho.
# ---------------------------------------------------------


# 1) run_type + custom name
@traceable(run_type="tool", name="Get Order Status")
def get_order_status(order_id: str) -> dict:
    time.sleep(0.3)  # fake DB call — UI mein latency dikhegi
    return {"order_id": order_id, "status": "shipped"}


# 2) Static tags + metadata (har call par same)
@traceable(
    run_type="chain",
    name="Format Reply",
    tags=["formatting", "v2"],
    metadata={"component": "reply_formatter", "version": "2.0"},
)
def format_reply(status: dict) -> str:
    return f"Aap ka order {status['order_id']} {status['status']} ho chuka hai."


# 3) Parent function: andar wale traceable functions iske CHILD runs ban jayenge
@traceable(name="Handle Customer Message")
def handle_message(message: str, order_id: str) -> str:
    status = get_order_status(order_id)
    return format_reply(status)


if __name__ == "__main__":
    # 4) Dynamic metadata/tags: call ke waqt `langsmith_extra` pass karo.
    #    Industry mein yahan user_id, session_id, request_id, prompt_version wagera aate hain.
    reply = handle_message(
        "Mera order kahan hai?",
        "ORD-1001",
        langsmith_extra={
            "metadata": {"user_id": "user_123", "channel": "whatsapp"},
            "tags": ["production-like"],
        },
    )
    print(reply)

    # Doosra call different user ke saath — UI mein metadata se filter karke dekho
    handle_message(
        "Order status?",
        "ORD-2002",
        langsmith_extra={"metadata": {"user_id": "user_456", "channel": "web"}},
    )
    print("Done. UI mein 'Handle Customer Message' trace kholo -> 2 child runs dikhenge.")
