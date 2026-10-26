"""
Prompt fetch + compile + OpenAI ke saath use + trace se link.

get_prompt options:
  label="production"   (default)    |  label="staging"
  version=2                         (specific version, testing ke liye)
  cache_ttl_seconds=300             (client cache; default 60s)
  fallback=[...]                    (Langfuse unreachable ho to yeh use hoga)

Link: OpenAI call mein langfuse_prompt=prompt -> UI mein prompt version-wise metrics.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from langfuse import get_client, observe  # noqa: E402
from langfuse.openai import OpenAI  # noqa: E402

langfuse = get_client()
client = OpenAI()

STORE = "Watch Store"
FAQ = "Delivery 1-2 din (Lahore), 3-5 din baqi Pakistan. Sirf COD. 7 din exchange. 6 mahine warranty."

FALLBACK_PROMPT = [
    {"role": "system", "content": "You are a support agent for {{store_name}}. FAQ:\n{{faq}}"},
    {"role": "user", "content": "{{question}}"},
]


def load_prompt(label: str = "production"):
    return langfuse.get_prompt(
        "watch-support",
        type="chat",
        label=label,
        cache_ttl_seconds=300,
        fallback=FALLBACK_PROMPT,
    )


@observe(name="answer-with-managed-prompt")
def answer(question: str, label: str = "production") -> str:
    prompt = load_prompt(label)
    messages = prompt.compile(store_name=STORE, faq=FAQ, question=question)  # list of chat messages

    config = prompt.config or {}
    resp = client.chat.completions.create(
        model=config.get("model", os.getenv("OPENAI_MODEL", "gpt-4o-mini")),
        temperature=config.get("temperature", 0),
        messages=messages,
        name="support-answer",
        # Link sirf asal prompt ka — fallback ka link nahi banta
        langfuse_prompt=None if prompt.is_fallback else prompt,
    )
    langfuse.update_current_span(
        metadata={"prompt_version": str(prompt.version), "fallback": str(prompt.is_fallback), "label": label}
    )
    return resp.choices[0].message.content


if __name__ == "__main__":
    q = "Card se payment ho sakti hai?"
    print("production:", answer(q, "production"))
    print("staging   :", answer(q, "staging"))

    # Text prompt bhi
    text = langfuse.get_prompt("product-description")
    print("\ntext prompt compiled:", text.compile(product_name="Black Chrono Watch", tone="premium"))

    langfuse.flush()
    print("\nUI: Prompts -> watch-support -> 'Metrics' tab: har version ki generations, latency, cost.")
