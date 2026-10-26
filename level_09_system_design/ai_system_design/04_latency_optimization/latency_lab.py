"""
Module 4 · Latency Lab
======================

Pehle NAAPO, phir optimize karo. Ye lab 6 experiments karti hai:

  1. Waterfall       : ek request ka waqt kahan ja raha hai (retrieval / tool / TTFT / generation)
  2. Streaming       : TTFT vs total. User ko "pehla lafz" kab dikhta hai
  3. Parallel        : independent kaam (order lookup + policy search + profile) sequential vs asyncio.gather
  4. Context size    : 500 vs 4k vs 12k input tokens -> TTFT par asar (prefill)
  5. Output length   : max_tokens / reasoning effort -> total time par asar
  6. Capacity math   : Little's Law: concurrency = QPS x latency; rate-limit (TPM) check

Chalane ka tareeqa (PowerShell, root folder, venv active):
    python 04_latency_optimization\\latency_lab.py --mock   # OFFLINE simulation (realistic delays)
    python 04_latency_optimization\\latency_lab.py          # REAL Groq (GROQ_API_KEY)

Note: Real mode ~15 chhoti API calls karta hai (free tier par theek hai).
"""

from __future__ import annotations

import argparse
import asyncio
import os
import statistics
import time
from contextlib import contextmanager
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()
MODEL = "openai/gpt-oss-20b"

# ==========================================================================
# Helpers: span timer (production mein yahi kaam tracing karta hai, M9.8)
# ==========================================================================


@dataclass
class Trace:
    spans: list[tuple[str, float, float]] = field(default_factory=list)  # (name, start, end)
    t0: float = field(default_factory=time.perf_counter)

    @contextmanager
    def span(self, name: str):
        s = time.perf_counter()
        try:
            yield
        finally:
            self.spans.append((name, s - self.t0, time.perf_counter() - self.t0))

    def waterfall(self, width: int = 50) -> None:
        total = max(e for _, _, e in self.spans)
        for name, s, e in self.spans:
            a, b = int(s / total * width), max(int(s / total * width) + 1, int(e / total * width))
            print(f"    {name:<22}{e - s:>6.2f}s |{' ' * a}{'█' * (b - a)}{' ' * (width - b)}|")
        print(f"    {'TOTAL':<22}{total:>6.2f}s")


# ==========================================================================
# LLM backends: REAL (Groq) aur MOCK (simulation with realistic physics)
# ==========================================================================


@dataclass
class LLMResult:
    ttft: float
    total: float
    out_tokens: int


class MockLLM:
    """
    Simple latency model jo real providers jaisa behave karta hai:
      TTFT  = queue/network base + prefill (input tokens par depend)
      total = TTFT + output_tokens / tokens_per_sec
    """

    def __init__(self, base=0.15, prefill_per_1k=0.025, tps=600):
        self.base, self.prefill_per_1k, self.tps = base, prefill_per_1k, tps

    async def call(self, prompt_tokens: int, max_tokens: int, effort: str = "low",
                   on_token=None) -> LLMResult:
        start = time.perf_counter()
        await asyncio.sleep(self.base + prompt_tokens / 1000 * self.prefill_per_1k)
        reasoning = {"low": 60, "medium": 250, "high": 700}[effort]
        out = min(max_tokens, reasoning + 120)
        ttft = time.perf_counter() - start
        for i in range(0, out, 20):                     # 20-token chunks stream karo
            await asyncio.sleep(20 / self.tps)
            if on_token and i >= reasoning:             # reasoning user ko nahi dikhti
                on_token()
        return LLMResult(ttft, time.perf_counter() - start, out)


class GroqLLM:
    def __init__(self):
        from groq import AsyncGroq

        self.client = AsyncGroq()

    async def call(self, prompt_tokens: int, max_tokens: int, effort: str = "low",
                   on_token=None) -> LLMResult:
        from groq import RateLimitError

        for attempt in range(4):
            try:
                return await self._call(prompt_tokens, max_tokens, effort, on_token)
            except RateLimitError:
                # Free tier ki TPM limit. Ye khud ek system-design sabaq hai (EXP 6).
                wait = 15 * (attempt + 1)
                print(f"    [429 rate limit] {wait}s wait karke retry...")
                await asyncio.sleep(wait)
        raise RuntimeError("Rate limit baar baar: thori der baad chalayein.")

    async def _call(self, prompt_tokens: int, max_tokens: int, effort: str,
                    on_token) -> LLMResult:
        filler = ("Policy note: returns within 7 days, delivery Lahore 1-2 days. " * 400)
        context = filler[: prompt_tokens * 4]            # ~4 chars per token
        start = time.perf_counter()
        ttft = None
        out_tokens = 0
        stream = await self.client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "system", "content": "Answer briefly."},
                      {"role": "user", "content": f"{context}\n\nSummarize the policy in 3 lines."}],
            max_completion_tokens=max_tokens,
            reasoning_effort=effort,
            stream=True,
        )
        async for chunk in stream:
            if chunk.choices:
                d = chunk.choices[0].delta
                if ttft is None and (d.content or getattr(d, "reasoning", None)):
                    ttft = time.perf_counter() - start
                if d.content and on_token:
                    on_token()
            xg = getattr(chunk, "x_groq", None)
            if xg is not None and getattr(xg, "usage", None):
                out_tokens = xg.usage.completion_tokens
        total = time.perf_counter() - start
        return LLMResult(ttft or total, total, out_tokens)


# ==========================================================================
# Simulated non-LLM work (retrieval, tools). Real system mein ye DB / API calls hain.
# ==========================================================================


async def retrieve_policies() -> str:
    await asyncio.sleep(0.25)        # vector + BM25 search
    return "policies"


async def get_order_status() -> str:
    await asyncio.sleep(0.60)        # Shopify API
    return "shipped"


async def get_customer_profile() -> str:
    await asyncio.sleep(0.40)        # DB lookup
    return "returning customer"


# ==========================================================================
# Experiments
# ==========================================================================


async def exp1_waterfall(llm) -> None:
    print("\n=== EXP 1: Waterfall: waqt kahan ja raha hai? (sequential pipeline) ===")
    tr = Trace()
    with tr.span("webhook+parse"):
        await asyncio.sleep(0.05)
    with tr.span("retrieval"):
        await retrieve_policies()
    with tr.span("tool: order status"):
        await get_order_status()
    with tr.span("tool: profile"):
        await get_customer_profile()
    with tr.span("LLM (ttft+generate)"):
        await llm.call(prompt_tokens=2500, max_tokens=300)
    with tr.span("send WhatsApp reply"):
        await asyncio.sleep(0.30)
    tr.waterfall()


async def exp2_streaming(llm) -> None:
    print("\n=== EXP 2: Streaming: perceived latency ===")
    first_visible = {}
    start = time.perf_counter()

    def on_tok():
        first_visible.setdefault("t", time.perf_counter() - start)

    r = await llm.call(prompt_tokens=1500, max_tokens=500, on_token=on_tok)
    fv = first_visible.get("t", r.total)
    print(f"    TTFT (pehla token, reasoning samet) : {r.ttft:.2f}s")
    print(f"    Pehla VISIBLE answer token          : {fv:.2f}s   <- streaming UI mein user ko yahan se dikhta hai")
    print(f"    Total (poora jawab)                 : {r.total:.2f}s   <- non-streaming / WhatsApp mein user itna wait karta hai")
    print("    Reasoning models mein pehla visible token reasoning ke BAAD aata hai, is liye")
    print("    effort kam rakhna streaming UX ke liye bhi zaroori hai.")


async def exp3_parallel(llm) -> None:
    print("\n=== EXP 3: Sequential vs parallel (independent kaam) ===")
    t = time.perf_counter()
    await retrieve_policies()
    await get_order_status()
    await get_customer_profile()
    seq = time.perf_counter() - t

    t = time.perf_counter()
    await asyncio.gather(retrieve_policies(), get_order_status(), get_customer_profile())
    par = time.perf_counter() - t
    print(f"    3 tools sequential : {seq:.2f}s")
    print(f"    3 tools parallel   : {par:.2f}s  (= sab se slow wala, ~0.60s)")

    # 3 independent LLM calls (e.g. intent, sentiment, language)
    t = time.perf_counter()
    for _ in range(3):
        await llm.call(prompt_tokens=300, max_tokens=150)
    seq_llm = time.perf_counter() - t
    t = time.perf_counter()
    await asyncio.gather(*[llm.call(prompt_tokens=300, max_tokens=150) for _ in range(3)])
    par_llm = time.perf_counter() - t
    print(f"    3 LLM calls sequential : {seq_llm:.2f}s")
    print(f"    3 LLM calls parallel   : {par_llm:.2f}s")
    print("    Aur behtar: teeno ko EK call mein karo (structured output: intent+sentiment+lang).")


async def exp4_context_size(llm) -> None:
    print("\n=== EXP 4: Context size -> TTFT (prefill) ===")
    # Real mode mein sizes chhote: Groq free tier ki tokens-per-minute limit ke andar rehne ke liye
    sizes = (500, 4000, 12000) if isinstance(llm, MockLLM) else (300, 1500, 5000)
    for n in sizes:
        ttfts = [(await llm.call(prompt_tokens=n, max_tokens=60)).ttft for _ in range(2)]
        print(f"    input ~{n:>6} tokens -> TTFT {statistics.mean(ttfts):.2f}s")
    print("    Groq jaise tez providers par farq chhota ho sakta hai, lekin COST linear badhti hai.")


async def exp5_output_length(llm) -> None:
    print("\n=== EXP 5: Output length & reasoning effort -> total time ===")
    for max_tok, effort in ((150, "low"), (600, "low"), (600, "medium")):
        r = await llm.call(prompt_tokens=800, max_tokens=max_tok, effort=effort)
        print(f"    max_tokens={max_tok:<4} effort={effort:<7} -> out {r.out_tokens:>4} tok, "
              f"total {r.total:.2f}s")
    print("    Generation time ~ output tokens. Chhota jawab = tez + sasta.")


def exp6_capacity() -> None:
    print("\n=== EXP 6: Capacity math (Little's Law) ===")
    peak_qps, latency_s, tokens_per_req = 2.0, 3.0, 3000
    concurrency = peak_qps * latency_s
    tpm = peak_qps * 60 * tokens_per_req
    rpm = peak_qps * 60
    print(f"    Peak {peak_qps} req/s x {latency_s}s latency  = {concurrency:.0f} requests ek saath 'in flight'")
    print(f"    -> server workers / async connections kam se kam {concurrency:.0f} chahiye")
    print(f"    Provider limits needed: ~{rpm:.0f} RPM, ~{tpm:,.0f} TPM")
    print("    Apne provider ke rate limits (console.groq.com/settings/limits) se compare karo.")
    print("    Limit se upar = 429 errors -> queue / fallback / dusra provider (M9.6).")


async def run(mock: bool) -> None:
    llm = MockLLM() if mock else GroqLLM()
    await exp1_waterfall(llm)
    await exp2_streaming(llm)
    await exp3_parallel(llm)
    await exp4_context_size(llm)
    await exp5_output_length(llm)
    exp6_capacity()


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--mock", action="store_true", help="offline simulation")
    args = p.parse_args()
    mock = args.mock or not os.getenv("GROQ_API_KEY")
    print(f"Mode: {'MOCK simulation (offline)' if mock else f'REAL Groq ({MODEL})'}")
    asyncio.run(run(mock))


if __name__ == "__main__":
    main()
