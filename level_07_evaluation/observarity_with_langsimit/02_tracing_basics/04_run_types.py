"""
Run types ko SAHI format mein log karna — taake UI unhein achhe se render kare.

  - retriever: list of {"page_content", "type": "Document", "metadata"} return karo
  - tool:      agent tools
  - llm:       agar tum khud LLM call kar rahe ho (wrapper nahi / koi aur provider),
               to messages format + ls_provider/ls_model_name metadata + usage_metadata do
               taake tokens aur cost UI mein aa jayein.
"""
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

FAKE_DB = [
    {"id": "faq-1", "text": "Delivery Lahore mein 2-3 din leti hai."},
    {"id": "faq-2", "text": "Payment sirf Cash on Delivery hai."},
    {"id": "faq-3", "text": "7 din ke andar exchange ho sakta hai."},
]


@traceable(run_type="retriever", name="FAQ Retriever")
def retrieve(query: str) -> list[dict]:
    words = query.lower().split()
    hits = [d for d in FAKE_DB if any(w in d["text"].lower() for w in words)]
    # Yeh format UI mein documents ko properly dikhata hai
    return [
        {"page_content": d["text"], "type": "Document", "metadata": {"id": d["id"]}}
        for d in hits
    ]


@traceable(run_type="tool", name="Calculator")
def calculator(expression: str) -> float:
    allowed = set("0123456789+-*/(). ")
    if not set(expression) <= allowed:
        raise ValueError("Invalid expression")
    return eval(expression)  # demo only — production mein eval mat use karna


@traceable(
    run_type="llm",
    name="Custom LLM",
    metadata={"ls_provider": "my_provider", "ls_model_name": "my-local-model"},
)
def fake_llm(messages: list[dict]) -> dict:
    """Maan lo yeh tumhara local/self-hosted model hai jiska wrapper nahi hai."""
    answer = "Delivery 2-3 din mein ho jati hai."
    return {
        "choices": [{"message": {"role": "assistant", "content": answer}}],
        # usage_metadata dene se UI mein tokens dikhte hain
        "usage_metadata": {"input_tokens": 25, "output_tokens": 9, "total_tokens": 34},
    }


@traceable(name="Mini RAG Pipeline")
def rag(question: str) -> str:
    docs = retrieve(question)
    context = "\n".join(d["page_content"] for d in docs)
    result = fake_llm(
        [
            {"role": "system", "content": f"Context:\n{context}"},
            {"role": "user", "content": question},
        ]
    )
    return result["choices"][0]["message"]["content"]


if __name__ == "__main__":
    print(rag("delivery kitne din"))
    print(calculator("(1500 * 2) + 200"))
    print("UI: retriever run mein documents list aur llm run mein tokens dekho.")
