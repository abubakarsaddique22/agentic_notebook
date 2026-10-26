"""
Prompt management: Prompt Hub se pull (cached) + local fallback.

Push karne ke liye (capstone folder se):
    python -m app.prompts
"""
from functools import lru_cache

from app.settings import PROMPT_ID, PROMPT_NAME, ls_client

from langchain_core.prompts import ChatPromptTemplate
# ---------------------------------------------------------
# ChatPromptTemplate  (langchain_core) -- placeholders wala chat prompt
#   from_messages([("system", "...{var}..."), ("human", "{question}")])
#   .invoke({vars}) -> PromptValue; LangSmith Prompt Hub pe isi ko push / pull karte hain.
# ---------------------------------------------------------

SYSTEM_TEMPLATE = """You are the customer support agent of {store_name}, a Pakistani online store for men's watches and wallets.

Rules:
1. Answer ONLY using the CONTEXT below. If the answer is not in the context, say you will forward the question to the team, or that you can only help with store-related questions.
2. Reply in Roman Urdu, maximum 2-3 short sentences, polite tone.
3. Never invent prices, policies, discounts or payment methods.

CONTEXT:
{context}"""

LOCAL_PROMPT = ChatPromptTemplate.from_messages([("system", SYSTEM_TEMPLATE), ("human", "{question}")])


@lru_cache(maxsize=1)
def get_prompt() -> tuple[ChatPromptTemplate, str]:
    """Returns (prompt, label). Label trace metadata mein jata hai taake pata rahe kaunsa prompt chala."""
    try:
        return ls_client.pull_prompt(PROMPT_ID), f"hub:{PROMPT_ID}"
    except Exception:
        return LOCAL_PROMPT, "local"


if __name__ == "__main__":
    try:
        url = ls_client.push_prompt(PROMPT_NAME, object=LOCAL_PROMPT, description="Capstone support bot prompt")
        print("Pushed:", url)
    except Exception as e:
        print("Push skip:", e)
