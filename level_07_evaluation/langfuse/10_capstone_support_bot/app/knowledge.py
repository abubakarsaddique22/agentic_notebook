"""
Knowledge base + retriever.

Simple keyword-overlap retriever (free, no embeddings) — focus Langfuse par hai.
Real project mein vector DB (Chroma / pgvector / Qdrant) lagao; @observe(as_type="retriever") wahi rahega.
"""
import json
import re
from functools import lru_cache

from app.settings import FAQ_PATH

from langfuse import observe


@lru_cache(maxsize=1)
def load_faq() -> list[dict]:
    with open(FAQ_PATH, encoding="utf-8") as f:
        return json.load(f)


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


@observe(name="faq-retriever", as_type="retriever")
def retrieve(query: str, k: int = 3) -> list[dict]:
    q = _tokens(query)
    scored = []
    for item in load_faq():
        vocab = set(item["keywords"]) | _tokens(item["question"])
        score = len(q & vocab)
        if score > 0:
            scored.append((score, item))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [
        {"id": item["id"], "question": item["question"], "answer": item["answer"], "score": score}
        for score, item in scored[:k]
    ]
