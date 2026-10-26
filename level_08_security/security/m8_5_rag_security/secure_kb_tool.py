"""The secure knowledge-base TOOL the agent actually gets.

Combines M8.5 (audience filter + poison scan + provenance) with M8.2 (fencing),
so the string handed to the model is both filtered AND clearly marked as data.
"""
from __future__ import annotations

from langchain_core.tools import tool

from m8_2_prompt_injection.defenses import fence_untrusted
from m8_5_rag_security.secure_retrieval import secure_search, format_for_model


def make_kb_tool(audience: str = "public"):
    """Return a search tool bound to a given audience (customer -> 'public')."""

    @tool
    def search_knowledge_base(query: str) -> str:
        """Search TimeHouse store policies (shipping, returns, warranty)."""
        chunks = secure_search(query, audience=audience, k=3)
        body = format_for_model(chunks)
        return fence_untrusted("STORE DOCUMENTS", body)

    return search_knowledge_base
