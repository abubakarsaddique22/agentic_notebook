"""Shared configuration: paths, the app LLM and the local Ollama embeddings.

Every module (app, guardrails, red teaming, tests) gets its models from here,
so switching a model is a one-line change in .env.

LLM_PROVIDER=groq    -> Groq openai/gpt-oss-120b (default)
LLM_PROVIDER=ollama  -> Ollama model (use for long attack runs: no Groq rate limits)
"""
import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama, OllamaEmbeddings

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

APP_DIR = ROOT / "app"
DATA_DIR = APP_DIR / "data"
DOCS_DIR = DATA_DIR / "docs"
CHROMA_DIR = ROOT / ".chroma"
OUTPUT_DIR = ROOT / "outputs"  # simulated side effects (emails, refunds) and run results
OUTPUT_DIR.mkdir(exist_ok=True)

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq").lower()
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
OLLAMA_APP_MODEL = os.getenv("OLLAMA_APP_MODEL", "gpt-oss:20b-cloud")
EMBED_MODEL = os.getenv("EMBED_MODEL", "all-minilm")
MODEL_LABEL = f"ollama/{OLLAMA_APP_MODEL}" if LLM_PROVIDER == "ollama" else f"groq/{GROQ_MODEL}"


@lru_cache(maxsize=4)
def get_llm(temperature: float = 0.0):
    """The application LLM (the model under attack)."""
    if LLM_PROVIDER == "ollama":
        return ChatOllama(model=OLLAMA_APP_MODEL, temperature=temperature)
    if not os.getenv("GROQ_API_KEY"):
        raise RuntimeError("GROQ_API_KEY is missing. Create .env from .env.example.")
    # max_retries lets the SDK back off and retry on Groq free-tier 429 rate limits.
    return ChatGroq(model=GROQ_MODEL, temperature=temperature, max_retries=5)


@lru_cache(maxsize=1)
def get_embeddings() -> OllamaEmbeddings:
    """Local embeddings via Ollama (no API cost, no data leaves the machine)."""
    return OllamaEmbeddings(model=EMBED_MODEL)


@lru_cache(maxsize=4)
def get_ollama_chat(temperature: float = 0.0) -> ChatOllama:
    """Local chat model (gpt-oss:20b-cloud) used for moderation and red teaming.
    Separate from get_llm so moderation stays independent of the app's provider."""
    return ChatOllama(model=OLLAMA_APP_MODEL, temperature=temperature)
