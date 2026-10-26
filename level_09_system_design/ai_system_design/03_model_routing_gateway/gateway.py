"""
Module 3 · Model Gateway + Routing + Cascade + Fallbacks (LiteLLM)
==================================================================

Industry pattern: application code KABHI seedha provider SDK call nahi karta.
Wo ek GATEWAY ko call karta hai, jo ye sab ek jagah karta hai:

    app code  ──►  gateway.chat(task="faq", tenant="shop_a", ...)
                      │  1. routing policy   : task/risk/size -> model alias ("fast"/"smart")
                      │  2. budget check     : tenant ka monthly budget
                      │  3. LiteLLM Router   : retries, timeout, FALLBACKS (fast -> smart -> local)
                      │  4. usage ledger     : tokens, cost, latency per tenant/feature
                      ▼
                  Groq gpt-oss-20b / Groq gpt-oss-120b / Ollama (local)

Model badalna ho? Sirf MODEL_LIST badlo. App code ko pata bhi nahi chalega.

Chalane ka tareeqa (PowerShell, root folder, venv active):
    python 03_model_routing_gateway\\gateway.py --mock    # OFFLINE: koi API call nahi (LiteLLM mock)
    python 03_model_routing_gateway\\gateway.py           # REAL: GROQ_API_KEY chahiye (Ollama optional)

Env (optional): OLLAMA_CHAT_MODEL (default gpt-oss:20b-cloud), OLLAMA_BASE_URL
"""

from __future__ import annotations

import argparse
import json
import os
import time
from collections import defaultdict
from dataclasses import dataclass, field

import litellm
from dotenv import load_dotenv
from litellm import Router

litellm.suppress_debug_info = True
# Fallback model kisi param (e.g. reasoning_effort) ko support na kare to error ki jagah drop kar do.
litellm.drop_params = True
load_dotenv()

# ==========================================================================
# 1) Model catalog: ALIASES. App sirf "fast" / "smart" / "local" jaanti hai.
# ==========================================================================

OLLAMA_MODEL = os.getenv("OLLAMA_CHAT_MODEL", "gpt-oss:20b-cloud")
OLLAMA_BASE = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

MODEL_LIST = [
    {"model_name": "fast",  "litellm_params": {"model": "groq/openai/gpt-oss-20b"}},
    {"model_name": "smart", "litellm_params": {"model": "groq/openai/gpt-oss-120b"}},
    {"model_name": "local", "litellm_params": {"model": f"ollama_chat/{OLLAMA_MODEL}",
                                               "api_base": OLLAMA_BASE}},
]

# Response mein provider ka model naam aata hai; wapas alias banane ke liye reverse map
ALIAS_BY_MODEL = {m["litellm_params"]["model"].split("/", 1)[1]: m["model_name"] for m in MODEL_LIST}

# Fallback chain: primary fail ho (outage / rate limit / timeout) to agla try karo.
FALLBACKS = [
    {"fast": ["smart", "local"]},
    {"smart": ["fast", "local"]},   # ⚠️ smart -> fast = QUALITY DOWNGRADE (notes section 5 dekho)
]


# ==========================================================================
# 2) Usage ledger: har call ka hisaab (LiteLLM success callback)
# ==========================================================================


@dataclass
class UsageRecord:
    tenant: str
    feature: str
    requested: str
    served_by: str
    prompt_tokens: int
    completion_tokens: int
    cost_usd: float
    latency_s: float


@dataclass
class UsageLedger:
    records: list[UsageRecord] = field(default_factory=list)

    def callback(self, kwargs, response, start_time, end_time) -> None:
        meta = (kwargs.get("litellm_params") or {}).get("metadata") or {}
        usage = getattr(response, "usage", None)
        self.records.append(UsageRecord(
            tenant=meta.get("tenant", "unknown"),
            feature=meta.get("feature", "unknown"),
            requested=meta.get("requested_alias", "?"),
            served_by=meta.get("model_group", "?"),
            prompt_tokens=getattr(usage, "prompt_tokens", 0) or 0,
            completion_tokens=getattr(usage, "completion_tokens", 0) or 0,
            cost_usd=kwargs.get("response_cost") or 0.0,
            latency_s=(end_time - start_time).total_seconds(),
        ))

    def spent(self, tenant: str) -> float:
        return sum(r.cost_usd for r in self.records if r.tenant == tenant)

    def report(self) -> None:
        print(f"\n  {'tenant':<10}{'feature':<14}{'calls':>6}{'tokens':>9}{'cost $':>12}"
              f"{'avg lat':>9}  served_by")
        groups: dict[tuple, list[UsageRecord]] = defaultdict(list)
        for r in self.records:
            groups[(r.tenant, r.feature)].append(r)
        for (tenant, feature), rs in sorted(groups.items()):
            served = ",".join(sorted({r.served_by for r in rs}))
            print(f"  {tenant:<10}{feature:<14}{len(rs):>6}"
                  f"{sum(r.prompt_tokens + r.completion_tokens for r in rs):>9}"
                  f"{sum(r.cost_usd for r in rs):>12.6f}"
                  f"{sum(r.latency_s for r in rs) / len(rs):>8.2f}s  {served}")


# ==========================================================================
# 3) Routing policy: kaun sa model? (deterministic, explainable)
# ==========================================================================


@dataclass
class RouteDecision:
    alias: str
    reason: str
    reasoning_effort: str = "low"
    needs_human_approval: bool = False


def choose_route(task: str, input_tokens: int = 500, risk: str = "low") -> RouteDecision:
    """
    Routing signals: task type, risk, context size (aur production mein: latency SLO,
    modality, tenant plan, language). Rules pehle; ML/LLM router tab jab rules kaafi na rahein.
    """
    if risk == "high":
        return RouteDecision("smart", "high-risk action: strongest model + human approval",
                             reasoning_effort="medium", needs_human_approval=True)
    if task in {"classify", "extract", "faq", "greeting"}:
        return RouteDecision("fast", f"'{task}' simple hai -> sasta/tez model")
    if task in {"complaint", "multi_step", "reasoning"}:
        return RouteDecision("smart", f"'{task}' mein nuance/reasoning chahiye",
                             reasoning_effort="medium")
    if input_tokens > 50_000:
        return RouteDecision("smart", "bohat lamba context -> stronger long-context model")
    return RouteDecision("fast", "default: cascade fast se shuru (M9.3 section 4)")


# ==========================================================================
# 4) The Gateway
# ==========================================================================


class BudgetExceeded(Exception):
    pass


class ModelGateway:
    def __init__(self, mock: bool, monthly_budget_usd: dict[str, float] | None = None) -> None:
        self.mock = mock
        self.ledger = UsageLedger()
        self.budgets = monthly_budget_usd or {}
        litellm.success_callback = [self.ledger.callback]
        if mock:
            os.environ.setdefault("GROQ_API_KEY", "mock-key")
        self.router = Router(
            model_list=MODEL_LIST,
            fallbacks=FALLBACKS,
            num_retries=2,          # transient errors par same model dobara (backoff ke saath)
            timeout=30,             # seconds. Kabhi bhi "forever wait" mat rakho
            allowed_fails=3,        # itne fails ke baad deployment cooldown mein (mini circuit breaker)
            cooldown_time=30,
        )

    def chat(self, messages: list[dict], *, task: str, tenant: str, feature: str,
             risk: str = "low", force_alias: str | None = None,
             mock_response: str | None = None, simulate_outage: bool = False,
             **params):
        # --- budget guard (cost control at the gateway, not in every feature) ---
        cap = self.budgets.get(tenant)
        degraded = False
        if cap is not None and self.ledger.spent(tenant) >= cap:
            if risk == "high":
                raise BudgetExceeded(f"{tenant} budget ${cap} khatam; high-risk request block")
            degraded = True   # graceful: sasta model, ya "baad mein try karein"

        decision = choose_route(task, risk=risk)
        alias = force_alias or ("fast" if degraded else decision.alias)

        extra = {}
        if self.mock:
            extra["mock_response"] = mock_response or f"[mock answer from {alias}]"
            if simulate_outage:
                extra["mock_testing_fallbacks"] = True   # primary ko fail karwa ke fallback test

        resp = self.router.completion(
            model=alias,
            messages=messages,
            reasoning_effort=decision.reasoning_effort,
            metadata={"tenant": tenant, "feature": feature, "requested_alias": alias},
            **extra,
            **params,
        )
        served_by = ALIAS_BY_MODEL.get(resp.model, resp.model)
        return resp, decision, alias, served_by, degraded


# ==========================================================================
# 5) Cascade: pehle sasta model; sirf zaroorat par mehnga
# ==========================================================================

CASCADE_SYSTEM = """You are a support assistant. Use ONLY the context.
Return JSON: {"answer": str, "answerable_from_context": bool, "confidence": "high"|"low"}"""


def validate(raw: str) -> tuple[bool, str, dict | None]:
    """Deterministic checks PEHLE. Model ki 'confidence' par akela bharosa mat karo."""
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return False, "invalid JSON", None
    if not isinstance(data.get("answer"), str) or not data["answer"].strip():
        return False, "empty answer", data
    if data.get("answerable_from_context") is False:
        return False, "model says not answerable", data
    if data.get("confidence") != "high":
        return False, "low confidence", data
    return True, "ok", data


def cascade(gw: ModelGateway, question: str, context: str, tenant: str,
            mock_fast: str | None = None, mock_smart: str | None = None) -> dict:
    msgs = [{"role": "system", "content": CASCADE_SYSTEM},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"}]
    fmt = {"response_format": {"type": "json_object"}, "temperature": 0.1,
           "max_completion_tokens": 400}

    r1, *_ = gw.chat(msgs, task="faq", tenant=tenant, feature="cascade", force_alias="fast",
                     mock_response=mock_fast, **fmt)
    ok, why, data = validate(r1.choices[0].message.content or "")
    if ok:
        return {"tier": "fast", "answer": data["answer"], "escalated": False, "why": why}

    r2, *_ = gw.chat(msgs, task="complaint", tenant=tenant, feature="cascade",
                     force_alias="smart", mock_response=mock_smart, **fmt)
    ok2, why2, data2 = validate(r2.choices[0].message.content or "")
    if ok2:
        return {"tier": "smart", "answer": data2["answer"], "escalated": True, "why": why}
    # Dono fail -> model se zabardasti jawab mat nikalo. Human ko do.
    return {"tier": "human", "answer": "Main aap ko hamari team se connect karta hoon.",
            "escalated": True, "why": f"{why} / {why2}"}


# ==========================================================================
# 6) Demos
# ==========================================================================

CONTEXT = ("Returns within 7 days if unused and in original box. Delivery Lahore 1-2 days. "
           "Warranty 6 months on movement only.")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--mock", action="store_true", help="offline: LiteLLM mock responses")
    args = p.parse_args()
    mock = args.mock or not os.getenv("GROQ_API_KEY")
    if mock and not args.mock:
        print("GROQ_API_KEY nahi mili -> MOCK mode (offline). Real ke liye .env mein key daalein.")
    print(f"Mode: {'MOCK (offline)' if mock else 'REAL (Groq)'}")

    gw = ModelGateway(mock=mock, monthly_budget_usd={"shop_b": 0.0})  # shop_b ka budget khatam

    # --- Demo 1: routing table ---
    print("\n=== DEMO 1: Routing policy ===")
    for task, risk in [("greeting", "low"), ("faq", "low"), ("classify", "low"),
                       ("complaint", "low"), ("refund", "high"), ("unknown", "low")]:
        d = choose_route(task, risk=risk)
        print(f"  task={task:<10} risk={risk:<5} -> {d.alias:<6} effort={d.reasoning_effort:<7}"
              f" approval={str(d.needs_human_approval):<5} | {d.reason}")

    msgs = [{"role": "user", "content": "Lahore mein delivery kitne din mein? 1 line mein."}]

    # --- Demo 2: normal call ---
    print("\n=== DEMO 2: Normal call (gateway -> fast) ===")
    r, d, alias, served, _ = gw.chat(msgs, task="faq", tenant="shop_a", feature="faq",
                                     mock_response="Lahore mein 1-2 working days.",
                                     max_completion_tokens=300)
    print(f"  requested={alias} served_by={served} | {r.choices[0].message.content!r}")

    # --- Demo 3: provider outage -> fallback ---
    print("\n=== DEMO 3: Primary fail -> fallback ===")
    if mock:
        r, d, alias, served, _ = gw.chat(msgs, task="faq", tenant="shop_a", feature="faq",
                                         mock_response="(fallback model ka jawab)",
                                         simulate_outage=True)
        print(f"  requested={alias} served_by={served}  <- user ko pata bhi nahi chala")
    else:
        print("  REAL mode mein outage simulate karne ke liye: MODEL_LIST mein 'fast' ka model naam")
        print("  galat kar do (e.g. groq/does-not-exist) aur dobara chalao. served_by 'smart' aayega.")

    # --- Demo 4: cascade ---
    print("\n=== DEMO 4: Cascade (fast -> validate -> smart -> human) ===")
    cases = [
        ("Return kitne din mein ho sakta hai?",
         '{"answer":"7 din mein, agar unused aur original box mein ho.","answerable_from_context":true,"confidence":"high"}',
         None),
        ("Meri watch ka strap toot gaya aur glass par crack hai, delivery ke 5 din baad. Kya karun?",
         '{"answer":"Shayad warranty...","answerable_from_context":true,"confidence":"low"}',
         '{"answer":"Strap aur glass warranty mein nahi. Lekin 7 din ke andar damaged item return ho sakta hai, original box ke saath.","answerable_from_context":true,"confidence":"high"}'),
        ("Kya aap Dubai deliver karte ho?",
         '{"answer":"","answerable_from_context":false,"confidence":"low"}',
         '{"answer":"Context mein info nahi.","answerable_from_context":false,"confidence":"low"}'),
    ]
    escalations = 0
    for q, m_fast, m_smart in cases:
        out = cascade(gw, q, CONTEXT, "shop_a", mock_fast=m_fast, mock_smart=m_smart)
        escalations += out["escalated"]
        print(f"  Q: {q[:60]!r}\n     -> tier={out['tier']:<5} why={out['why']:<26} A: {out['answer'][:80]!r}")
    print(f"  Escalation rate: {escalations}/{len(cases)}. Production mein ye metric track karo (M9.8).")

    # --- Demo 5: budget guard ---
    print("\n=== DEMO 5: Tenant budget guard ===")
    r, d, alias, served, degraded = gw.chat(msgs, task="complaint", tenant="shop_b",
                                            feature="faq", mock_response="(degraded answer)")
    print(f"  shop_b budget khatam -> 'complaint' normally '{d.alias}' jata, "
          f"lekin '{alias}' diya gaya (degraded={degraded})")
    try:
        gw.chat(msgs, task="refund", tenant="shop_b", feature="refund", risk="high")
    except BudgetExceeded as e:
        print(f"  high-risk request blocked: {e}")

    # --- Ledger ---
    time.sleep(0.5)  # callbacks async ho sakte hain
    print("\n=== USAGE LEDGER (gateway ka asal faida: ek jagah poora hisaab) ===")
    gw.ledger.report()
    if mock:
        print("\n  (Mock mode: tokens/cost LiteLLM ke farzi numbers hain. Real mode mein asli aayenge.)")


if __name__ == "__main__":
    main()
