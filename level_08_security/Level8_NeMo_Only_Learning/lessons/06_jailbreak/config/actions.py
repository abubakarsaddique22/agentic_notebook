"""NeMo custom action for an experimental *lightweight* perplexity check.

Built-in `jailbreak detection heuristics` requires gpt2-large; this is
an alternative learning exercise, not an equivalent validated detector.
"""
import asyncio
import os
from functools import lru_cache
from typing import Optional

from nemoguardrails.actions import action

MODEL_ID = "distilgpt2"


@lru_cache(maxsize=1)
def _get_model():
    from transformers import AutoModelForCausalLM, AutoTokenizer
    model = AutoModelForCausalLM.from_pretrained(MODEL_ID)
    model.eval()
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
    return tokenizer, model


def _perplexity(text: str) -> float:
    import torch
    tokenizer, model = _get_model()
    batch = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
    if batch["input_ids"].shape[1] < 2:
        return 1.0
    with torch.inference_mode():
        loss = model(**batch, labels=batch["input_ids"]).loss
    return float(torch.exp(loss).item())


@action(name="check_lightweight_jailbreak")
async def check_lightweight_jailbreak(context: Optional[dict] = None) -> bool:
    """Experimental perplexity flag; NOT a trained jailbreak classifier.

    Optional JAILBREAK_PPL_THRESHOLD must be calibrated on benign and
    adversarial prompts for this model. Without a threshold, detection
    is observation-only: self-check input remains the enforcing rail.
    """
    message = (context or {}).get("user_message", "")
    if not message.strip():
        return False
    try:
        ppl = await asyncio.to_thread(_perplexity, message)
        print(f"[NeMo distilgpt2] perplexity={ppl:.2f}", flush=True)
        threshold = os.getenv("JAILBREAK_PPL_THRESHOLD", "").strip()
        return bool(threshold) and ppl > float(threshold)
    except Exception as exc:
        # Do not silently swallow model errors: self-check still enforces policy,
        # but show the optional detector's failure prominently.
        print(f"[NeMo distilgpt2] detector unavailable: {exc}", flush=True)
        return False
