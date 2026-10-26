"""
Support bot ka core logic.

Langfuse concepts jo yahan use ho rahe hain:
  - @observe + observation types (chain, retriever)       (folder 02)
  - langfuse.openai drop-in                                 (folder 02)
  - propagate_attributes: session_id, user_id, tags, version (folder 02/04)
  - environment + release + masking + sampling              (folder 04, settings.py)
  - managed prompt + fallback + prompt<->generation link    (folder 07, prompts.py)
  - automatic score (has_context) + user feedback score     (folder 08)
  - trace_id wapas client ko (feedback ke liye)             (folder 08)
"""
from dataclasses import dataclass, field

from app.settings import APP_NAME, APP_VERSION, MAX_HISTORY_MESSAGES, MODEL, STORE_NAME, langfuse

from app.knowledge import retrieve
from app.prompts import LOCAL_CONFIG, get_prompt
from langfuse import observe, propagate_attributes
from langfuse.openai import OpenAI

oai = OpenAI()

# Demo ke liye memory mein. Production: Redis / Postgres.
_HISTORY: dict[str, list[dict]] = {}


@dataclass
class ChatResult:
    answer: str
    trace_id: str | None
    sources: list[str] = field(default_factory=list)


@observe(name="support-bot", as_type="chain")
def respond(question: str, history: list[dict] | None = None) -> dict:
    """Pure logic: question (+history) -> answer. Evals bhi isi ko call karte hain."""
    docs = retrieve(question)
    context = "\n\n".join(f"Q: {d['question']}\nA: {d['answer']}" for d in docs) or "No relevant FAQ found."

    prompt = get_prompt()
    messages = prompt.compile(store_name=STORE_NAME, context=context, question=question)
    # system + (pichli baatein) + current question
    messages = messages[:1] + (history or []) + messages[1:]

    config = prompt.config or LOCAL_CONFIG
    resp = oai.chat.completions.create(
        model=config.get("model", MODEL),
        temperature=config.get("temperature", 0.2),
        messages=messages,
        name="support-answer",
        langfuse_prompt=None if prompt.is_fallback else prompt,
    )
    answer = resp.choices[0].message.content

    # Knowledge gaps pakarne ke liye: context na mila to score 0 -> UI mein filter "has_context = 0"
    langfuse.score_current_trace(name="has_context", value=1.0 if docs else 0.0, data_type="BOOLEAN")
    langfuse.update_current_span(
        metadata={
            "num_docs": len(docs),
            "prompt_version": "fallback" if prompt.is_fallback else str(prompt.version),
        }
    )
    return {"answer": answer, "sources": [d["id"] for d in docs]}


@observe(name="chat-turn")
def chat(question: str, session_id: str, user_id: str) -> ChatResult:
    """App ka entry point (API / CLI / WhatsApp webhook yahan call karein)."""
    with propagate_attributes(
        session_id=session_id,
        user_id=user_id,
        tags=[APP_NAME],
        version=APP_VERSION,
    ):
        history = _HISTORY.setdefault(session_id, [])
        out = respond(question, history[-MAX_HISTORY_MESSAGES:])
        trace_id = langfuse.get_current_trace_id()

    history.append({"role": "user", "content": question})
    history.append({"role": "assistant", "content": out["answer"]})
    return ChatResult(answer=out["answer"], trace_id=trace_id, sources=out["sources"])


def record_feedback(trace_id: str, score: int, comment: str | None = None) -> None:
    """User 👍 (1) / 👎 (0)."""
    langfuse.create_score(
        trace_id=trace_id,
        name="user_rating",
        value=float(score),
        data_type="BOOLEAN",
        comment=comment,
    )
