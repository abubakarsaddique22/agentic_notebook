"""
Scores: user feedback + automatic checks.

  1. Request handle karte waqt trace_id nikaalo, response ke saath client ko bhejo
  2. Code ke andar automatic score: score_current_trace()
  3. User baad mein click kare -> create_score(trace_id=...)
  4. Poori conversation par score -> create_score(session_id=...)
"""
import os
import uuid
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from langfuse import get_client, observe, propagate_attributes  # noqa: E402
from langfuse.openai import OpenAI  # noqa: E402

MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
langfuse = get_client()
client = OpenAI()


@observe(name="support-reply")
def handle_request(question: str, session_id: str) -> dict:
    with propagate_attributes(session_id=session_id, user_id="customer-77"):
        resp = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "Watch store support. Only COD. Reply in 1 line."},
                {"role": "user", "content": question},
            ],
            name="reply",
        )
        answer = resp.choices[0].message.content

        # 2) Automatic score — code check (har trace par)
        langfuse.score_current_trace(
            name="mentions_cod",
            value=1.0 if "cod" in answer.lower() or "cash on delivery" in answer.lower() else 0.0,
            data_type="BOOLEAN",
        )
        trace_id = langfuse.get_current_trace_id()

    return {"answer": answer, "trace_id": trace_id}  # 1) trace_id client ko wapas


if __name__ == "__main__":
    session = f"session-{uuid.uuid4().hex[:6]}"
    r1 = handle_request("Kya JazzCash se payment ho sakti hai?", session)
    r2 = handle_request("Delivery charges?", session)
    print(r1, "\n", r2)

    # 3) User feedback (real app mein /feedback endpoint se aata hai)
    langfuse.create_score(trace_id=r1["trace_id"], name="user_rating", value=1.0, data_type="BOOLEAN", comment="Helpful")
    langfuse.create_score(trace_id=r2["trace_id"], name="user_rating", value=0.0, data_type="BOOLEAN", comment="Charges nahi bataye")
    langfuse.create_score(trace_id=r2["trace_id"], name="feedback_reason", value="missing_info", data_type="CATEGORICAL")
    langfuse.create_score(trace_id=r2["trace_id"], name="stars", value=2.0, data_type="NUMERIC")

    # 4) Session (poori conversation) score — e.g. "masla hal hua?"
    langfuse.create_score(session_id=session, name="resolved", value=0.0, data_type="BOOLEAN")

    langfuse.flush()
    print("\nTrace link:", langfuse.get_trace_url(trace_id=r2["trace_id"]))
    print("UI: Traces list mein Scores column; filter 'user_rating = 0'. Sessions tab mein 'resolved' score.")
