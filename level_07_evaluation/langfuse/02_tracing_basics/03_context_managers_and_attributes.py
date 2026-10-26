"""
Decorator ke ilawa tracing + trace-level attributes.

  1. start_as_current_observation(...)  -> code ke ek block ko observation banana
  2. propagate_attributes(...)          -> user_id, session_id, tags, metadata, version
                                           har child observation par (v3 ka update_current_trace ab nahi hai)
  3. get_current_trace_id() / get_trace_url() -> trace ki ID / link (logs, feedback, support tickets ke liye)
  4. LANGFUSE_TRACING_ENABLED=false -> tracing band (tests mein)
"""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from langfuse import get_client, observe, propagate_attributes  # noqa: E402
from langfuse.openai import OpenAI  # noqa: E402

MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
langfuse = get_client()
client = OpenAI()


@observe(name="classify-intent")
def classify_intent(text: str) -> str:
    return "order_status" if "order" in text.lower() else "general"


def process_batch(messages: list[str]) -> list[str]:
    # 1) Context manager: poore function ko decorate kiye bina ek block trace karna
    with langfuse.start_as_current_observation(
        as_type="span",
        name="batch-processing",
        input={"count": len(messages)},
    ) as span:
        results = [classify_intent(m) for m in messages]
        span.update(output={"intents": results}, metadata={"batch_size": len(messages)})
    return results


@observe(name="support-request")
def support_request(user_id: str, session_id: str, question: str) -> dict:
    # 2) Root function ke shuru mein hi attributes propagate karo
    #    -> is ke andar banne wali har observation (OpenAI generation bhi) par lagenge
    with propagate_attributes(
        user_id=user_id,
        session_id=session_id,
        tags=["v2", "support"],
        metadata={"channel": "whatsapp", "plan": "free"},  # values string honi chahiye
        version="2.1.0",
        trace_name="support-request",
    ):
        intent = classify_intent(question)
        resp = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": f"(intent: {intent}) {question}. 1 line mein jawab do."}],
            name="support-answer",
        )

        # 3) Trace ID — isko API response mein bhejo (feedback ke liye, folder 08)
        trace_id = langfuse.get_current_trace_id()

    return {"answer": resp.choices[0].message.content, "trace_id": trace_id}


if __name__ == "__main__":
    print(process_batch(["Mera order kahan hai?", "Shop kab khulti hai?"]))

    result = support_request("user_123", "session-abc", "Mera order kab aayega?")
    print(result["answer"])
    print("Trace URL:", langfuse.get_trace_url(trace_id=result["trace_id"]))

    langfuse.flush()
    print("\nUI: Traces mein tags 'v2' filter karo, aur 'Users' tab mein user_123 dekho.")
