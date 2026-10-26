"""
Step 2: Pehla trace.

Part A: Sirf Python functions (koi paisa nahi lagta).
Part B: OpenAI call — Langfuse ka drop-in OpenAI client tokens + cost khud track karta hai.

Key idea: @observe() lagao -> function ka input, output, time, error sab Langfuse mein.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from langfuse import get_client, observe  # noqa: E402
from langfuse.openai import OpenAI  # noqa: E402  <- sirf import badla, baqi OpenAI SDK same

MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
langfuse = get_client()
openai_client = OpenAI()


# ---------------- Part A: Plain Python ----------------
@observe()  # function ka naam observation ka naam ban jata hai
def add_tax(price: float) -> float:
    return round(price * 1.17, 2)


@observe()
def checkout(items: list[float]) -> dict:
    subtotal = sum(items)
    total = add_tax(subtotal)  # child observation (nested)
    return {"subtotal": subtotal, "total_with_tax": total}


# ---------------- Part B: OpenAI ----------------
@observe(name="ask-question")  # custom naam
def ask(question: str) -> str:
    response = openai_client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "You are a helpful assistant. Answer in 2 lines."},
            {"role": "user", "content": question},
        ],
        name="answer-generation",  # Langfuse-only kwarg: generation ka naam
    )
    return response.choices[0].message.content


if __name__ == "__main__":
    print("Part A:", checkout([1000, 2500, 499]))
    print("Part B:", ask("Langfuse kya hai?"))

    langfuse.flush()  # script khatam hone se pehle sab bhej do
    print("\nAb cloud.langfuse.com -> Tracing mein 2 traces dekho: 'checkout' aur 'ask-question'.")
