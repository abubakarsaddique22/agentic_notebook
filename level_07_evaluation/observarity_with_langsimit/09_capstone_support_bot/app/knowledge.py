"""
Knowledge base + retriever.

Simple keyword-overlap retriever (free, no embeddings) — focus LangSmith par hai.
Real project mein isko vector DB (Chroma / pgvector / Pinecone) se replace karo;
@traceable(run_type="retriever") wahi rahega.
"""
import json
import re
from functools import lru_cache

from app.settings import FAQ_PATH

from langsmith import traceable
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


@lru_cache(maxsize=1)
def load_faq() -> list[dict]:
    with open(FAQ_PATH, encoding="utf-8") as f:
        return json.load(f)


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


@traceable(run_type="retriever", name="FAQ Retriever")
def retrieve(query: str, k: int = 3) -> list[dict]:
    q = _tokens(query)
    scored = []
    for item in load_faq():
        vocab = set(item["keywords"]) | _tokens(item["question"])
        score = len(q & vocab)
        if score > 0:
            scored.append((score, item))
    scored.sort(key=lambda x: x[0], reverse=True)

    # Retriever ka standard output format (UI mein documents properly dikhte hain)
    return [
        {
            "page_content": f"Q: {item['question']}\nA: {item['answer']}",
            "type": "Document",
            "metadata": {"id": item["id"], "score": score},
        }
        for score, item in scored[:k]
    ]
