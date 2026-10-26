"""
judge.py -- RAGAS ka shared JUDGE (LLM + embeddings), poore project ke liye ek jagah.

RAGAS v0.4 (collections API):
    - LLM banane ka ek hi tareeka: llm_factory(model, client=...)
    - metrics ko judge constructor ma milta ha:  Faithfulness(llm=judge_llm)
    - score:  result = await metric.ascore(...)  ->  result.value, result.reason

Sab kuch OLLAMA pe:
    - Judge LLM  = gpt-oss:20b-cloud  (Ollama ka OpenAI-compatible /v1 endpoint)
    - Embeddings = local Ollama embedding model (sirf AnswerRelevancy ko chahiye)
      Wahi model jo retriever use karta ha (OLLAMA_EMBED_MODEL, default all-minilm).
"""

import os

from dotenv import load_dotenv
from openai import AsyncOpenAI
from ragas.embeddings import embedding_factory
# ---------------------------------------------------------
# embedding_factory  (function -- RAGAS ke liye embeddings object banata ha)
#   embedding_factory(provider, model, client, interface)
#     provider  -> "openai" (Ollama ka /v1 OpenAI-compatible ha, is liye yahi)
#     model     -> embedding model ka naam (all-minilm, nomic-embed-text)
#     client    -> AsyncOpenAI client (ascore andar aembed_text() await karta ha)
#     interface -> "modern" = naya RAGAS 0.4 embeddings class (collections metrics
#                  sirf yahi qubool karte hain), "legacy" = purana, "auto" = khud chuno
#   Return: BaseRagasEmbedding -> .embed_text() / .aembed_text()
#   Kaun use karta ha: AnswerRelevancy aur SemanticSimilarity (cosine similarity).
# ---------------------------------------------------------
from ragas.llms import llm_factory
# ---------------------------------------------------------
# llm_factory  (function -- RAGAS judge LLM banata ha)
#   llm_factory(model, provider="openai", client=..., adapter="auto", cache=None, **kwargs)
#     model    -> judge model ka naam (gpt-oss:20b-cloud)
#     provider -> "openai" -- Ollama /v1 OpenAI jaisa ha
#     client   -> pehle se bana client (ZAROORI). AsyncOpenAI -> ascore() async chalta ha
#     adapter  -> structured output kaise: "instructor" (default auto) ya "litellm"
#     cache    -> (optional) DiskCacheBackend() do to same prompt ka jawab cache
#                 -> dobara run sasta + tez
#     **kwargs -> model settings: max_tokens, temperature, reasoning_effort waghera
#   Return: InstructorBaseRagasLLM -> .generate() / .agenerate(). Ye instructor
#   library se judge ka jawab pydantic schema (JSON) ma lata ha -- metrics isi
#   structured output se verdicts parhte hain.
#   DeepEval ma ye kaam DeepEvalBaseLLM wali custom class karti thi; RAGAS ma
#   factory function hi kaafi ha.
# ---------------------------------------------------------

load_dotenv()

JUDGE_MODEL = os.getenv("JUDGE_MODEL", "gpt-oss:20b-cloud")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY", "ollama")   # local Ollama key check nahi karta
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "all-minilm:latest")


def get_judge_llm():
    """RAGAS judge LLM (async client -- metrics .ascore() isi ko use karte hain)."""
    client = AsyncOpenAI(
        base_url=OLLAMA_BASE_URL,
        api_key=OLLAMA_API_KEY,
        timeout=300,        # cloud reasoning model kabhi kabhi slow hota ha
        max_retries=3,
    )
    return llm_factory(
        JUDGE_MODEL,    # judge model ka naam
        provider="openai",          # Ollama /v1 = OpenAI-compatible
        client=client,    # AsyncOpenAI client (Ollama /v1)
        # gpt-oss reasoning model ha: pehle "sochta" ha phir JSON deta ha.
        # RAGAS ka default max_tokens (1024) kam pad sakta ha -> JSON beech ma kat jata ha.
        max_tokens=8192,
        reasoning_effort="low",
    )


def get_judge_embeddings(model: str | None = None):
    """Embeddings for AnswerRelevancy / SemanticSimilarity. RAGAS ascore() andar aembed_text()
    call karta ha -> ASYNC client zaroori.
    model=None -> OLLAMA_EMBED_MODEL (all-minilm: chhote sawalon ke liye kaafi).
    Lambe answers compare karne hon to bada context wala model do (nomic-embed-text)."""
    client = AsyncOpenAI(base_url=OLLAMA_BASE_URL, api_key=OLLAMA_API_KEY)
    return embedding_factory("openai", model=model or OLLAMA_EMBED_MODEL, client=client, interface="modern")


def judge_info() -> dict:
    """Experiment results ke saath log karne ke liye config."""
    return {
        "judge_model": JUDGE_MODEL,
        "judge_embed_model": OLLAMA_EMBED_MODEL,   # sirf judge ka (AnswerRelevancy), RAG app ka nahi
    }
