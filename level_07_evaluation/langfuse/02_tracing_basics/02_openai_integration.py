"""
Langfuse OpenAI drop-in integration.

  from openai import OpenAI          ->   from langfuse.openai import OpenAI

Seekho:
  1. Normal call + Langfuse kwargs (name, metadata)
  2. Streaming (include_usage se tokens bhi)
  3. JSON output — @observe pipeline ke andar
"""
import json
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from langfuse import get_client, observe  # noqa: E402
from langfuse.openai import OpenAI  # noqa: E402

MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
langfuse = get_client()
client = OpenAI()  # ek dafa banao, poori app mein use karo


def normal_call() -> str:
    # @observe ke bina bhi yeh call apna trace banayegi (generation)
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": "Ek line mein: observability kya hai?"}],
        name="observability-definition",  # Langfuse kwarg: generation ka naam
        metadata={"feature": "faq"},  # Langfuse kwarg: generation ka metadata
    )
    return resp.choices[0].message.content


def streaming_call() -> str:
    stream = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": "3 watch brands ke naam batao."}],
        stream=True,
        stream_options={"include_usage": True},  # streaming mein bhi token count
        name="streaming-demo",
    )
    full = ""
    for chunk in stream:
        if chunk.choices:  # aakhri usage-chunk mein choices khali hoti hain
            piece = chunk.choices[0].delta.content or ""
            full += piece
            print(piece, end="", flush=True)
    print()
    return full


@observe(name="extract-order-info")
def extract_order_info(customer_text: str) -> dict:
    """LLM se structured JSON — real projects mein bohat common."""
    resp = client.chat.completions.create(
        model=MODEL,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": 'Extract JSON: {"product": str, "quantity": int, "city": str}'},
            {"role": "user", "content": customer_text},
        ],
        name="order-extractor",
    )
    return json.loads(resp.choices[0].message.content)


if __name__ == "__main__":
    print("1)", normal_call())
    print("2) Streaming:")
    streaming_call()
    print("3)", extract_order_info("Mujhe 2 black watches chahiye, Lahore delivery"))
    langfuse.flush()
    print("\nUI: generation kholo -> model, tokens, cost. 'extract-order-info' ke andar nested generation.")
