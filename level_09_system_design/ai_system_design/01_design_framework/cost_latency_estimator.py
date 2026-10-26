"""
Module 1 · Cost & Latency Estimator (back-of-envelope calculator)
==================================================================

Kya karta hai:
    Ek AI feature ka rough hisaab:
      - ek request ki cost
      - roz / mahine ki cost (USD + PKR)
      - average aur peak traffic (QPS)
      - ek jawab mein kitna waqt lagega (latency breakdown)
    ...aur alag models / scenarios ko side-by-side compare karta hai.

Kyun:
    System design ka pehla sawal hota hai: "kitna load, kitna budget, kitni speed?"
    Ye script koi API call NAHI karti. Sirf hisaab hai, is liye free hai aur turant chalti hai.
    Real numbers ke liye pehle `measure_baseline.py` chalayein, phir wahan se aaye
    token counts yahan SCENARIOS mein daal dein.

Chalane ka tareeqa (PowerShell, venv active):
    python 01_design_framework\\cost_latency_estimator.py

Numbers kahan se aaye:
    Groq prices: GroqCloud models docs, Oct 2026
      gpt-oss-20b : $0.075 in / $0.30 out per 1M tokens, ~1000 tok/s
      gpt-oss-120b: $0.15  in / $0.60 out per 1M tokens
      Cached input tokens par 50% discount.
    Speed (tok/s) aur TTFT ke kuch numbers ANDAAZA hain (comment mein likha hai).
    Prices badalte rehte hain, client ko quote dene se pehle hamesha check karein:
    https://console.groq.com/docs/models
"""

from __future__ import annotations

from dataclasses import dataclass, replace

# --------------------------------------------------------------------------
# 1) Models: price + speed
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class ModelSpec:
    name: str
    input_per_m: float          # USD per 1M input tokens
    output_per_m: float         # USD per 1M output tokens
    cached_input_per_m: float   # USD per 1M cached input tokens (prompt caching)
    output_tps: float           # output tokens per second (generation speed)
    ttft_s: float               # time to first token (seconds)


MODELS = {
    "groq/gpt-oss-20b": ModelSpec(
        name="groq/gpt-oss-20b",
        input_per_m=0.075, output_per_m=0.30, cached_input_per_m=0.0375,
        output_tps=1000,   # Groq listed speed
        ttft_s=0.30,       # ANDAAZA: measure_baseline.py se real number lein
    ),
    "groq/gpt-oss-120b": ModelSpec(
        name="groq/gpt-oss-120b",
        input_per_m=0.15, output_per_m=0.60, cached_input_per_m=0.075,
        output_tps=500,    # ANDAAZA
        ttft_s=0.40,       # ANDAAZA
    ),
    # Comparison ke liye ek "mehnga frontier model" (FARZI numbers, sirf seekhne ke liye).
    # Real frontier models ki prices provider ki site se check karein.
    "example/frontier-model": ModelSpec(
        name="example/frontier-model",
        input_per_m=3.00, output_per_m=15.00, cached_input_per_m=0.30,
        output_tps=80,
        ttft_s=0.80,
    ),
}

USD_TO_PKR = 280  # ANDAAZA: aaj ka rate check karke update karein

# WhatsApp Business Platform (Meta): 1 Oct 2026 se SERVICE messages (24h window ke andar replies)
# per-message charge hote hain, har business number ko 1,000/month FREE ke baad.
# Rate recipient ke country par depend karta hai (Pakistan = alag market, utility rate).
# Meta rate card se Pakistan ka rate le kar yahan daalein (abhi 0.0 = unknown):
WHATSAPP_SERVICE_RATE_USD = 0.0
WHATSAPP_FREE_SERVICE_MSGS = 1_000


# --------------------------------------------------------------------------
# 2) Scenario: aapka use case
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Scenario:
    name: str
    requests_per_day: int
    # --- input tokens per request (jo hum model ko bhejte hain) ---
    system_prompt_tokens: int   # instructions, persona, rules
    context_tokens: int         # FAQ / RAG chunks / product data
    history_tokens: int         # pichli chat
    user_tokens: int            # customer ka message
    # --- output tokens per request (jo model likhta hai) ---
    visible_output_tokens: int  # jo customer ko dikhta hai
    reasoning_tokens: int       # reasoning models andar "sochte" hain. Ye bhi bill hote hain!
    # --- baqi ---
    cached_input_fraction: float = 0.0   # input ka kitna hissa prompt-cache se aaya (0..1)
    peak_multiplier: float = 5.0         # peak traffic, average ka kitna guna
    busy_hours_per_day: float = 12.0     # traffic asal mein kitne ghanton mein aata hai
    retrieval_s: float = 0.0             # RAG search ka waqt
    network_overhead_s: float = 0.5      # internet + WhatsApp/Meta API + server
    streaming: bool = False              # WhatsApp par streaming NAHI hoti, web chat par hoti hai

    @property
    def input_tokens(self) -> int:
        return (self.system_prompt_tokens + self.context_tokens
                + self.history_tokens + self.user_tokens)

    @property
    def output_tokens(self) -> int:
        return self.visible_output_tokens + self.reasoning_tokens


# --------------------------------------------------------------------------
# 3) Calculations
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Estimate:
    cost_per_request: float
    cost_per_day: float
    cost_per_month: float
    avg_qps: float
    peak_qps: float
    latency_total_s: float
    latency_perceived_s: float      # user ko pehla lafz kab dikhta hai
    breakdown: dict[str, float]


def estimate(s: Scenario, m: ModelSpec) -> Estimate:
    # ---- cost ----
    cached = s.input_tokens * s.cached_input_fraction
    uncached = s.input_tokens - cached
    cost_in = (uncached * m.input_per_m + cached * m.cached_input_per_m) / 1_000_000
    cost_out = s.output_tokens * m.output_per_m / 1_000_000
    per_req = cost_in + cost_out

    # ---- traffic ----
    avg_qps = s.requests_per_day / (s.busy_hours_per_day * 3600)
    peak_qps = avg_qps * s.peak_multiplier

    # ---- latency ----
    reasoning_s = s.reasoning_tokens / m.output_tps
    answer_s = s.visible_output_tokens / m.output_tps
    breakdown = {
        "retrieval": s.retrieval_s,
        "ttft": m.ttft_s,
        "reasoning": reasoning_s,
        "answer_generation": answer_s,
        "network": s.network_overhead_s,
    }
    total = sum(breakdown.values())
    # Streaming ho to user ko pehla lafz answer generation se pehle dikh jata hai.
    perceived = total - answer_s if s.streaming else total

    return Estimate(
        cost_per_request=per_req,
        cost_per_day=per_req * s.requests_per_day,
        cost_per_month=per_req * s.requests_per_day * 30,
        avg_qps=avg_qps,
        peak_qps=peak_qps,
        latency_total_s=total,
        latency_perceived_s=perceived,
        breakdown=breakdown,
    )


# --------------------------------------------------------------------------
# 4) Pretty printing
# --------------------------------------------------------------------------


def print_scenario_header(s: Scenario) -> None:
    print("=" * 78)
    print(f"SCENARIO: {s.name}")
    print("=" * 78)
    print(f"  Requests/day        : {s.requests_per_day:,}")
    print(f"  Input tokens/req    : {s.input_tokens:,}  "
          f"(system {s.system_prompt_tokens} + context {s.context_tokens} + "
          f"history {s.history_tokens} + user {s.user_tokens})")
    print(f"  Output tokens/req   : {s.output_tokens:,}  "
          f"(visible {s.visible_output_tokens} + reasoning {s.reasoning_tokens})")
    print(f"  Cached input        : {s.cached_input_fraction:.0%}")
    print(f"  Streaming           : {'yes' if s.streaming else 'no (WhatsApp)'}")


def print_model_table(s: Scenario, model_keys: list[str]) -> None:
    header = (f"  {'Model':<24}{'$/request':>12}{'$/month':>11}"
              f"{'PKR/month':>12}{'latency':>10}{'peak QPS':>10}")
    print()
    print(header)
    print("  " + "-" * (len(header) - 2))
    for key in model_keys:
        e = estimate(s, MODELS[key])
        print(f"  {key:<24}{e.cost_per_request:>12.6f}{e.cost_per_month:>11.2f}"
              f"{e.cost_per_month * USD_TO_PKR:>12,.0f}"
              f"{e.latency_perceived_s:>9.2f}s{e.peak_qps:>10.3f}")


def print_latency_breakdown(s: Scenario, model_key: str) -> None:
    e = estimate(s, MODELS[model_key])
    print(f"\n  Latency breakdown ({model_key}):")
    for part, secs in e.breakdown.items():
        bar = "#" * max(1, round(secs * 20)) if secs > 0 else ""
        print(f"    {part:<18}{secs:>6.2f}s  {bar}")
    print(f"    {'TOTAL':<18}{e.latency_total_s:>6.2f}s")
    if s.streaming:
        print(f"    {'user ko pehla lafz':<18}{e.latency_perceived_s:>6.2f}s  (streaming ki wajah se)")


# --------------------------------------------------------------------------
# 5) Scenarios: yahan apne numbers daalein
# --------------------------------------------------------------------------

# Example: ek watch store ka WhatsApp support bot.
# Numbers ANDAAZE hain. measure_baseline.py chala kar real token counts se replace karein.
WHATSAPP_BOT = Scenario(
    name="WhatsApp support bot: baseline (poora FAQ prompt mein)",
    requests_per_day=1_000,
    system_prompt_tokens=800,
    context_tokens=1_500,      # poora FAQ + policies prompt mein daal diya
    history_tokens=500,
    user_tokens=50,
    visible_output_tokens=150,
    reasoning_tokens=150,      # gpt-oss reasoning model hai, reasoning_effort="low" ke saath
    retrieval_s=0.0,           # baseline mein koi RAG nahi
    network_overhead_s=0.8,    # WhatsApp Cloud API + webhook + server
    streaming=False,
)


def main() -> None:
    models = list(MODELS.keys())

    # --- A) Baseline: teeno models compare ---
    print_scenario_header(WHATSAPP_BOT)
    print_model_table(WHATSAPP_BOT, models)
    print_latency_breakdown(WHATSAPP_BOT, "groq/gpt-oss-20b")

    # --- B) What-if: traffic 10x ho jaye (sale season) ---
    sale = replace(WHATSAPP_BOT, name="What-if: traffic 10x (sale season)",
                   requests_per_day=10_000)
    print()
    print_scenario_header(sale)
    print_model_table(sale, models)

    # --- C) What-if: context trim + history limit (prompt chhota karna) ---
    trimmed = replace(WHATSAPP_BOT, name="What-if: sirf relevant FAQ (RAG) + history limit",
                      context_tokens=400, history_tokens=200, retrieval_s=0.15)
    print()
    print_scenario_header(trimmed)
    print_model_table(trimmed, models)

    # --- D) What-if: prompt caching (system prompt har dafa same hai) ---
    cached = replace(WHATSAPP_BOT, name="What-if: prompt caching (~30% input cached)",
                     cached_input_fraction=0.30)
    print()
    print_scenario_header(cached)
    print_model_table(cached, models)

    # --- E) Seekhne wali baat: output tokens kitne mehnge hain ---
    base = estimate(WHATSAPP_BOT, MODELS["groq/gpt-oss-20b"])
    s_in = WHATSAPP_BOT.input_tokens * MODELS["groq/gpt-oss-20b"].input_per_m / 1e6
    s_out = WHATSAPP_BOT.output_tokens * MODELS["groq/gpt-oss-20b"].output_per_m / 1e6
    print("\n" + "=" * 78)
    print("SABAQ (gpt-oss-20b, baseline):")
    print(f"  Input  {WHATSAPP_BOT.input_tokens:>5} tokens -> ${s_in:.6f}  "
          f"({s_in / base.cost_per_request:.0%} of cost)")
    print(f"  Output {WHATSAPP_BOT.output_tokens:>5} tokens -> ${s_out:.6f}  "
          f"({s_out / base.cost_per_request:.0%} of cost)")
    ratio = WHATSAPP_BOT.input_tokens / WHATSAPP_BOT.output_tokens
    print(f"  Output tokens input se ~{ratio:.0f}x kam hain, phir bhi cost ka "
          f"{s_out / base.cost_per_request:.0%} hain,")
    print("  kyunke ek output token, input token se 4x mehnga hai.")
    if s_in > s_out:
        print("  Is use case mein INPUT zyada cost kar raha hai, to sab se bara lever:")
        print("  context chhota karo (RAG se sirf relevant FAQ, history limit, caching).")
    else:
        print("  Is use case mein OUTPUT zyada cost kar raha hai, to lever:")
        print("  jawab chhota karo, max_tokens set karo, reasoning_effort kam karo.")
    print("=" * 78)

    # --- F) Channel cost: aksar LLM se ZYADA ---
    print("\nCHANNEL COST (WhatsApp service replies, per month):")
    for per_day in (150, 1_000, 10_000):
        for replies_per_msg in (1, 3):
            sent = per_day * 30 * replies_per_msg
            billable = max(0, sent - WHATSAPP_FREE_SERVICE_MSGS)
            fee = billable * WHATSAPP_SERVICE_RATE_USD
            llm = estimate(replace(WHATSAPP_BOT, requests_per_day=per_day),
                           MODELS["groq/gpt-oss-20b"]).cost_per_month
            fee_txt = f"${fee:,.2f}" if WHATSAPP_SERVICE_RATE_USD else f"{billable:,} x rate"
            print(f"  {per_day:>6}/day, {replies_per_msg} reply/msg -> billable {billable:>8,} "
                  f"-> fee {fee_txt:<18} | LLM ${llm:,.2f}")
    print("  Sabaq: har customer message ka EK combined reply bhejo. 3 chhote messages = 3x billable messages.")
    if not WHATSAPP_SERVICE_RATE_USD:
        print("  (WHATSAPP_SERVICE_RATE_USD set nahi: Meta ke rate card se Pakistan ka rate daalein)")


if __name__ == "__main__":
    main()
