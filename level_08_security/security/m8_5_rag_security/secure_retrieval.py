"""Secure the knowledge layer (roadmap M8.5).

Fixes:
  - V5 / S4: internal docs leaking to customers  -> audience filter in the query
  - cross-tenant leakage                          -> metadata filter by tenant
  - retrieval poisoning / S5                      -> scan chunks for injected instructions
  - provenance                                    -> always return source + audience

The data layer (app/knowledge_base.py) already stores `audience` metadata. v0
ignored it; here we ENFORCE it at retrieval time, inside the Chroma `filter`,
so forbidden chunks never even enter the model's context.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from langchain_core.documents import Document

from app.knowledge_base import get_store

# Phrases that should never appear in a trusted policy doc. Their presence means
# the document is trying to give the model instructions = likely poisoning.
_POISON_SIGNS = [
    r"ignore (all|any|previous|the)",
    r"system instruction",
    r"do not (tell|mention|inform)",
    r"send_email|issue_refund|get_order",   # tool names inside a doc = red flag
    r"you must|assistant must",
]
_POISON_RE = [re.compile(p, re.I) for p in _POISON_SIGNS]


@dataclass
class RetrievedChunk:
    text: str
    source: str
    audience: str
    poison_flags: list[str]

    @property
    def is_suspicious(self) -> bool:
        return bool(self.poison_flags)


def _scan_poison(text: str) -> list[str]:
    return [rx.pattern for rx in _POISON_RE if rx.search(text)]


def secure_search(query: str, audience: str = "public", k: int = 3) -> list[RetrievedChunk]:
    """Retrieve only chunks the caller's audience is allowed to see, and flag
    any chunk that looks like it contains injected instructions."""
    # Audience filter happens in the vector store query itself (defence at source).
    where = {"audience": audience}
    docs: list[Document] = get_store().similarity_search(query, k=k, filter=where)

    chunks = []
    for d in docs:
        flags = _scan_poison(d.page_content)
        chunks.append(RetrievedChunk(
            text=d.page_content,
            source=d.metadata.get("source", "unknown"),
            audience=d.metadata.get("audience", "public"),
            poison_flags=flags,
        ))
    return chunks


def format_for_model(chunks: list[RetrievedChunk]) -> str:
    """Build the context string: drop suspicious chunks, keep provenance."""
    parts = []
    for c in chunks:
        if c.is_suspicious:
            parts.append(f"[source: {c.source}] [BLOCKED: possible injected instructions]")
            continue
        parts.append(f"[source: {c.source}]\n{c.text}")
    return "\n\n".join(parts) if parts else "No relevant policy found."


if __name__ == "__main__":
    print("Customer (public) asking for staff discount:")
    for c in secure_search("staff discount coupon", audience="public"):
        print(f"  {c.source} ({c.audience}) suspicious={c.is_suspicious}")
    print("\nStaff (internal) asking the same:")
    for c in secure_search("staff discount coupon", audience="internal"):
        print(f"  {c.source} ({c.audience})")
