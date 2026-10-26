"""
Prompt management: Langfuse se fetch (cache + fallback).

Prompt Langfuse par push karne ke liye (capstone folder se):
    python -m app.prompts
"""
from app.settings import PROMPT_LABEL, PROMPT_NAME, langfuse

SYSTEM_TEMPLATE = (
    "You are the customer support agent of {{store_name}}, a Pakistani online store for men's "
    "watches and wallets.\n\n"
    "Rules:\n"
    "1. Answer ONLY using the CONTEXT below. If the answer is not in the context, say you will "
    "forward the question to the team, or that you can only help with store-related questions.\n"
    "2. Reply in Roman Urdu, maximum 2-3 short sentences, polite tone.\n"
    "3. Never invent prices, policies, discounts or payment methods.\n\n"
    "CONTEXT:\n{{context}}"
)

LOCAL_PROMPT = [
    {"role": "system", "content": SYSTEM_TEMPLATE},
    {"role": "user", "content": "{{question}}"},
]

LOCAL_CONFIG = {"temperature": 0.2}


def get_prompt():
    """Langfuse se prompt (5 min cache). Langfuse down ho to LOCAL_PROMPT (is_fallback=True)."""
    return langfuse.get_prompt(
        PROMPT_NAME,
        type="chat",
        label=PROMPT_LABEL,
        cache_ttl_seconds=300,
        fallback=LOCAL_PROMPT,
    )


if __name__ == "__main__":
    p = langfuse.create_prompt(
        name=PROMPT_NAME,
        type="chat",
        prompt=LOCAL_PROMPT,
        labels=["production"],
        config=LOCAL_CONFIG,
        commit_message="capstone: initial prompt",
    )
    print(f"Pushed {p.name} v{p.version} labels={p.labels}")
