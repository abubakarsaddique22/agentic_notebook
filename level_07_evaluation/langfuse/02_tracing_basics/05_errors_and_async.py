"""
1. Errors: @observe wale function mein exception aaye to observation ka level ERROR ho jata hai
   aur error message save hota hai. Production debugging ka sabse bara faida.
2. Warnings: exception ke bina bhi level="WARNING" set kar sakte ho (e.g. fallback use hua).
3. Async: @observe async functions par bhi kaam karta hai; parallel calls sahi parent ke neeche nest hoti hain.
"""
import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from langfuse import get_client, observe  # noqa: E402
from langfuse.openai import AsyncOpenAI  # noqa: E402

MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
langfuse = get_client()
aclient = AsyncOpenAI()


# ---------- 1) Errors + 2) Warnings ----------
@observe(name="payment-gateway", as_type="tool")
def charge_card(amount: int) -> str:
    if amount > 10000:
        raise RuntimeError("Gateway timeout: amount too large")
    return "charged"


@observe(name="checkout")
def checkout(amount: int) -> str:
    try:
        return charge_card(amount)
    except RuntimeError as e:
        # Child ERROR mein hai; parent ko WARNING mark karo kyunke fallback chala
        langfuse.update_current_span(level="WARNING", status_message=f"fallback to COD: {e}")
        return "fallback: COD selected"


# ---------- 3) Async + parallel ----------
@observe(name="translate")
async def translate(text: str, lang: str) -> str:
    resp = await aclient.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": f"Translate to {lang}, only output translation: {text}"}],
        name=f"translate-{lang.lower()}",
    )
    return resp.choices[0].message.content


@observe(name="translate-to-many")
async def translate_many(text: str) -> dict:
    langs = ["Urdu", "Arabic", "French"]
    results = await asyncio.gather(*(translate(text, l) for l in langs))
    return dict(zip(langs, results))


if __name__ == "__main__":
    print(checkout(500))
    print(checkout(50000))  # UI: child laal (ERROR), parent peela (WARNING)
    print(asyncio.run(translate_many("Your order has been shipped.")))
    langfuse.flush()
    print("UI: 'translate-to-many' ke andar 3 parallel children — timeline view dekho.")
