"""
Module 1 · Baseline measurement (real Groq calls)
=================================================

Kya karta hai:
    "Baseline before sophistication" ko practically karta hai.
    Sab se SIMPLE design banata hai: ek system prompt + poora FAQ prompt mein, koi RAG nahi,
    koi agent nahi. Phir 8 test sawal bhej kar ye NAAPTA hai:
      - TTFT (pehla token kab aaya)
      - total latency
      - input / output / reasoning tokens
      - har request ki cost
      - quality: kitne jawab sahi the (simple keyword check)
    Aakhir mein p50/p95 latency aur total cost ka summary deta hai.

Kyun:
    Aap RAG ya agent tabhi lagate ho jab baseline FAIL ho, aur pata ho KAHAN fail hua.
    Ye numbers cost_latency_estimator.py mein daal kar aap mahine ka budget nikaal sakte ho.

Chalane ka tareeqa (PowerShell, venv active, .env mein GROQ_API_KEY ho):
    python 01_design_framework\\measure_baseline.py
    python 01_design_framework\\measure_baseline.py --model openai/gpt-oss-120b
    python 01_design_framework\\measure_baseline.py --effort medium

Note: Ye FAQ ek FARZI "Demo Watch Store" ka hai. Apne client ka data daal kar dobara chalayein.
"""

from __future__ import annotations

import argparse
import os
import statistics
import time
from dataclasses import dataclass

from dotenv import load_dotenv
from groq import Groq

# Prices: GroqCloud docs, Oct 2026 (USD per 1M tokens). Badlein to yahan update karein.
PRICES = {
    "openai/gpt-oss-20b": (0.075, 0.30),
    "openai/gpt-oss-120b": (0.15, 0.60),
}

# --------------------------------------------------------------------------
# Baseline "knowledge": poora FAQ seedha prompt mein (stuffing)
# --------------------------------------------------------------------------
FAQ = """
DEMO WATCH STORE: FAQ & POLICIES
- Delivery: Lahore 1-2 working days, rest of Pakistan 3-5 working days.
- Delivery charges: Rs 200 flat. Free delivery on orders above Rs 5,000.
- Payment: Cash on Delivery (COD) only. No card payments.
- Returns: 7 days from delivery, only if unused and in original box. Customer pays return shipping
  unless the item is damaged or wrong.
- Exchange: allowed within 7 days for a different model of same or higher price.
- Warranty: 6 months on movement (machine). No warranty on strap, glass, or water damage.
- Water resistance: "3ATM" means splash-proof only, not for swimming. "10ATM" is OK for swimming.
- Order tracking: share your order number (e.g. #1234); an agent will check it.
- Working hours: Mon-Sat, 11am-8pm. Messages outside hours are answered next working day.
- Gift wrapping: available for Rs 150.
"""

SYSTEM_PROMPT = f"""You are the WhatsApp support assistant for Demo Watch Store (Pakistan).
Rules:
- Answer ONLY from the FAQ below. If the answer is not in the FAQ, say you will connect
  the customer to a human agent. Never invent prices, dates, or policies.
- Reply in the customer's language (English or Roman Urdu). Keep replies under 60 words.
- Never ask for card details or passwords.

FAQ:
{FAQ}
"""

# --------------------------------------------------------------------------
# Test set: sawal + wo keywords jo sahi jawab mein hone chahiye.
# "must_include_any": in mein se koi ek bhi aa jaye to pass.
# Ye ek bohat simple eval hai. Level 7 wali DeepEval yahan baad mein lagayenge.
# --------------------------------------------------------------------------
TESTS = [
    ("Lahore mein delivery kitne din mein hoti hai?", ["1-2", "1 se 2", "1–2", "1 to 2"]),
    ("Do you accept credit card?", ["cash on delivery", "cod", "no card", "only cash"]),
    ("Kya main is watch ke saath swimming kar sakta hoon? Ye 3ATM hai", ["splash", "nahi", "not", "no"]),
    ("Delivery charges kitne hain? mera order 6000 ka hai", ["free"]),
    ("I want to return my watch, I used it for 2 days", ["unused", "original box", "not eligible", "nahi"]),
    ("Strap toot gaya hai, warranty mein aayega?", ["no warranty", "nahi", "not covered", "strap"]),
    ("Gift wrap ho sakta hai?", ["150"]),
    # Ye FAQ mein NAHI hai: bot ko human ke paas bhejna chahiye, invent nahi karna.
    ("Kya aap ke paas Rolex Submariner hai stock mein?", ["agent", "human", "connect", "team"]),
]


@dataclass
class Result:
    question: str
    answer: str
    ttft_s: float
    total_s: float
    input_tokens: int
    output_tokens: int
    reasoning_tokens: int
    cost_usd: float
    passed: bool


def run_one(client: Groq, model: str, effort: str, question: str, keywords: list[str]) -> Result:
    start = time.perf_counter()
    first_token_at: float | None = None
    answer_parts: list[str] = []
    usage = None

    stream = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": question},
        ],
        temperature=0.2,
        max_completion_tokens=600,     # reasoning + answer dono isi limit mein aate hain
        reasoning_effort=effort,       # "low" | "medium" | "high"
        stream=True,
    )

    for chunk in stream:
        if chunk.choices:
            delta = chunk.choices[0].delta
            # Pehla token: reasoning ya content, jo bhi pehle aaye
            if first_token_at is None and (delta.content or getattr(delta, "reasoning", None)):
                first_token_at = time.perf_counter()
            if delta.content:
                answer_parts.append(delta.content)
        # Groq streaming mein usage aakhri chunk ke x_groq mein aata hai
        x_groq = getattr(chunk, "x_groq", None)
        if x_groq is not None and getattr(x_groq, "usage", None) is not None:
            usage = x_groq.usage

    end = time.perf_counter()
    answer = "".join(answer_parts).strip()

    in_tok = getattr(usage, "prompt_tokens", 0) or 0
    out_tok = getattr(usage, "completion_tokens", 0) or 0
    details = getattr(usage, "completion_tokens_details", None)
    reasoning_tok = (getattr(details, "reasoning_tokens", 0) or 0) if details else 0

    price_in, price_out = PRICES.get(model, (0.0, 0.0))
    cost = (in_tok * price_in + out_tok * price_out) / 1_000_000

    passed = any(k.lower() in answer.lower() for k in keywords)

    return Result(
        question=question,
        answer=answer,
        ttft_s=(first_token_at - start) if first_token_at else end - start,
        total_s=end - start,
        input_tokens=in_tok,
        output_tokens=out_tok,
        reasoning_tokens=reasoning_tok,
        cost_usd=cost,
        passed=passed,
    )


def percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    k = (len(ordered) - 1) * p
    lo, hi = int(k), min(int(k) + 1, len(ordered) - 1)
    return ordered[lo] + (ordered[hi] - ordered[lo]) * (k - lo)


def main() -> None:
    parser = argparse.ArgumentParser(description="Measure a simple prompt-stuffing baseline on Groq.")
    parser.add_argument("--model", default="openai/gpt-oss-20b", choices=list(PRICES))
    parser.add_argument("--effort", default="low", choices=["low", "medium", "high"])
    args = parser.parse_args()

    load_dotenv()
    if not os.getenv("GROQ_API_KEY"):
        raise SystemExit("GROQ_API_KEY nahi mili. .env file check karein.")

    client = Groq()
    print(f"Model: {args.model} | reasoning_effort: {args.effort} | tests: {len(TESTS)}\n")

    results: list[Result] = []
    for i, (q, kws) in enumerate(TESTS, 1):
        try:
            r = run_one(client, args.model, args.effort, q, kws)
        except Exception as exc:  # noqa: BLE001: baseline script, sab errors dikhana hai
            print(f"[{i}] ERROR: {type(exc).__name__}: {exc}\n")
            continue
        results.append(r)
        status = "PASS" if r.passed else "FAIL"
        print(f"[{i}] {status} | ttft {r.ttft_s:.2f}s | total {r.total_s:.2f}s | "
              f"in {r.input_tokens} / out {r.output_tokens} (reasoning {r.reasoning_tokens}) | "
              f"${r.cost_usd:.6f}")
        print(f"    Q: {r.question}")
        print(f"    A: {r.answer[:220]}{'...' if len(r.answer) > 220 else ''}\n")

    if not results:
        return

    ttfts = [r.ttft_s for r in results]
    totals = [r.total_s for r in results]
    passed = sum(r.passed for r in results)
    avg_cost = statistics.mean(r.cost_usd for r in results)

    print("=" * 70)
    print("BASELINE SUMMARY")
    print("=" * 70)
    print(f"  Quality (keyword pass)  : {passed}/{len(results)} = {passed / len(results):.0%}")
    print(f"  TTFT    p50 / p95       : {percentile(ttfts, .5):.2f}s / {percentile(ttfts, .95):.2f}s")
    print(f"  Latency p50 / p95       : {percentile(totals, .5):.2f}s / {percentile(totals, .95):.2f}s")
    print(f"  Avg input tokens        : {statistics.mean(r.input_tokens for r in results):.0f}")
    print(f"  Avg output tokens       : {statistics.mean(r.output_tokens for r in results):.0f}"
          f"  (reasoning {statistics.mean(r.reasoning_tokens for r in results):.0f})")
    print(f"  Avg cost / request      : ${avg_cost:.6f}")
    print(f"  -> 1,000 req/day x 30   : ${avg_cost * 1000 * 30:.2f} / month (LLM cost only)")
    print("=" * 70)
    print("Next: ye avg tokens cost_latency_estimator.py ke WHATSAPP_BOT scenario mein daalein.")
    print("Note: ye latency sirf Groq ki hai. WhatsApp/network ka ~0.5-1s alag se add hoga.")


if __name__ == "__main__":
    main()
