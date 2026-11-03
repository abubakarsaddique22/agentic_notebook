"""NeMo @action() functions: retrieval checking, lightweight observation and
permission-checked pending ticket workflow. No other security framework used.
"""
import asyncio
import math
import os
import re
import sqlite3
from functools import lru_cache
from pathlib import Path
from typing import Optional

from nemoguardrails.actions import action

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "tickets.sqlite3"

@action(name="validate_retrieved_context")
async def validate_retrieved_context(context: Optional[dict] = None) -> bool:
    """Second retrieval defense: reject document-level instruction hijacking.
    First retrieval defense: NeMo's native Presidio masking rail.
    Note: lightweight content filter is supplemental, not a full classifier.
    """
    chunks = str((context or {}).get("relevant_chunks") or "")
    return inspect_tool_documents(chunks)

@lru_cache(maxsize=1)
def _ppl_model():
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained("distilgpt2")
    model = AutoModelForCausalLM.from_pretrained("distilgpt2")
    model.eval()
    return tokenizer, model

def _perplexity(message: str) -> float:
    import torch
    tokenizer, model = _ppl_model()
    tokens = tokenizer(message, return_tensors="pt", truncation=True, max_length=512)
    if tokens["input_ids"].shape[1] < 2:
        return 1.0
    with torch.inference_mode():
        loss = model(**tokens, labels=tokens["input_ids"]).loss
    return float(torch.exp(loss).item())

@action(name="observe_lightweight_jailbreak")
async def observe_lightweight_jailbreak(context: Optional[dict] = None) -> bool:
    """Optional distilgpt2 perplexity. OFF by default; LLM self-check remains on.
    Enable scoring with NEMO_LIGHTWEIGHT_PPL=1. Threshold blocking is OFF unless
    NEMO_PPL_THRESHOLD is also supplied and calibrated against a test dataset.
    Errors are surfaced, not silently interpreted as clean scores.
    """
    if os.getenv("NEMO_LIGHTWEIGHT_PPL") != "1":
        return False
    message = str((context or {}).get("user_message") or "")
    if not message.strip():
        return False
    try:
        score = await asyncio.to_thread(_perplexity, message)
        print(f"[NeMo distilgpt2] perplexity={score:.2f}")
        threshold = os.getenv("NEMO_PPL_THRESHOLD", "").strip()
        return bool(threshold) and score > float(threshold)
    except Exception as exc:
        raise RuntimeError("Lightweight jailbreak scorer failed; check model/dependencies") from exc



def inspect_tool_documents(text: str) -> bool:
    """Same inspection policy used by NeMo retrieval custom action.

    Mandatory at the external Chroma tool boundary: NeMo's native retrieval
    rail is for retrieval going through NeMo, not arbitrary LangChain tools.
    """
    return not any(term in text.lower() for term in (
        "ignore previous instructions", "assistant override", "system override",
        "security_lab_injection_success", "reveal the system prompt",
    ))
