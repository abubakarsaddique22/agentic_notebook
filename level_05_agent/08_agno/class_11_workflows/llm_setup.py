"""
=====================================================================
 HELPER FILE: llm_setup.py   (ye file har class folder mein same copy hai)
=====================================================================
 CONCEPT: Model connection (LLM) + Embedder
 Kya hai : Agno mein har Agent ko ek "model" (LLM) chahiye. Ye file
           .env parh ke sahi model object bana deti hai:
             get_model()    -> Groq / OpenRouter / Ollama / Gemini
             get_embedder() -> text ko vectors mein badalne wala
                               (Knowledge / RAG ke liye)
 Kyun    : Har file mein API key aur model ka naam likhne ki zaroorat
           nahi. Provider badalna ho to sirf .env mein LLM_PROVIDER badlo.

 Use:
     from llm_setup import get_model
     agent = Agent(model=get_model())
=====================================================================
"""

import os

from dotenv import load_dotenv

load_dotenv()  # course root wali .env parh lo


def get_model():
    """.env ke LLM_PROVIDER ke hisaab se model object deta hai."""
    provider = os.getenv("LLM_PROVIDER", "ollama").lower()

    if provider == "groq":
        from agno.models.groq import Groq
        return Groq(id=os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"))   # GROQ_API_KEY khud parhta hai

    if provider == "openrouter":
        from agno.models.openrouter import OpenRouter
        # OpenRouter mein naam "company/model" hota hai, e.g. openai/gpt-4o-mini
        return OpenRouter(id=os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini"))

    if provider == "ollama":
        from agno.models.ollama import Ollama
        return Ollama(
            id=os.getenv("OLLAMA_MODEL", "gpt-oss:20b-cloud"),
            host=os.getenv("OLLAMA_URL", "http://localhost:11434"),
        )

    if provider == "gemini":
        from agno.models.google import Gemini
        return Gemini(id=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"))  # GOOGLE_API_KEY

    raise ValueError(
        f"LLM_PROVIDER='{provider}' samajh nahi aaya. groq / openrouter / ollama / gemini likho."
    )


def get_embedder():
    """Knowledge (RAG) ke liye embedder. Default: FastEmbed (local, free, key nahi chahiye)."""
    provider = os.getenv("EMBEDDER_PROVIDER", "fastembed").lower()

    if provider == "ollama":
        from agno.knowledge.embedder.ollama import OllamaEmbedder
        # pehle: ollama pull nomic-embed-text   (is model ke 768 dimensions hain)
        return OllamaEmbedder(id=os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text"), dimensions=768)

    from agno.knowledge.embedder.fastembed import FastEmbedEmbedder
    # BAAI/bge-small-en-v1.5 -> 384 dimensions, pehli dafa ~70MB download
    return FastEmbedEmbedder()
