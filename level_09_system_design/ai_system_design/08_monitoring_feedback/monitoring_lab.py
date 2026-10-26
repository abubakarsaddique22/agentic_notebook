"""
Module 8 · Monitoring Lab: deploy -> observe -> feedback -> evaluate -> improve
==============================================================================

Ye script 14 din ka "production" simulate karti hai (WhatsApp support bot), phir ek
on-call engineer ki tarah usse ANALYZE karti hai.

Kahani (script ko pata hai, aap ko report se DHOONDNA hai):
  - Din 1-7  : app v1.4, prompt support-v3, retrieval hybrid-k3
  - Din 8    : DEPLOY v1.5 -> prompt support-v4 ("max 25 words") + reranker
               -> kuch sawalon ka jawab bigar gaya (kaun se? report batayegi)
  - Din 11   : Groq ~2 ghante down -> fallback model par traffic

Steps:
  1. SIMULATE  : traces + explicit feedback (thumbs) + implicit signals (rephrase, asked_human)
  2. DASHBOARD : daily metrics (volume, p95, cost, bad-rate, fallback %, cache %)
  3. COMPARE   : version vs version, phir version x intent (regression kahan hai?)
  4. ALERTS    : rule-based alerts vs 7-day baseline + SLOs
  5. TRIAGE    : top failing examples (versions ke saath)
  6. EXPORT    : failures -> eval candidates (JSON + CSV) -> Level 7 DeepEval set mein

Chalane ka tareeqa (PowerShell, root folder, venv active):
    python 08_monitoring_feedback\\monitoring_lab.py
Output files: 08_monitoring_feedback\\output\\  (traces.db, eval_candidates.json, label_me.csv)
"""

from __future__ import annotations

import csv
import json
import random
import re
import statistics
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from tracer import TraceRecord, Tracer, hash_user  # noqa: E402

OUT = Path(__file__).resolve().parent / "output"
SLO_P95_MS = 4000
PRICE_IN, PRICE_OUT = 0.075 / 1e6, 0.30 / 1e6

# --------------------------------------------------------------------------
# Traffic model
# --------------------------------------------------------------------------

INTENTS = {
    # intent: (weight, example queries, retrieved ids)
    "faq_returns": (25, ["Return policy kya hai?", "Can I return my watch?", "Wapas kaise karun?"],
                    ["returns@v2"]),
    "faq_delivery": (22, ["Karachi delivery kitne din?", "Islamabad mein kab tak aayega?",
                          "Delivery charges kitne hain?", "Lahore delivery time?"],
                     ["delivery@v1"]),
    "order_status": (20, ["Order #12345 kahan hai?", "Mera order #5521 status?"], []),
    "warranty": (12, ["Warranty kitni hai?", "Strap toot gaya, warranty?"], ["warranty@v1"]),
    "complaint": (8, ["Watch kharab nikli!!", "Bohat late delivery hui, gussa hoon"], []),
    "unknown": (13, ["Blue dial hai?", "Kya aap Dubai bhejte ho?", "Gift wrap?"], ["delivery@v1"]),
}


def p_bad(intent: str, version: str, level: str) -> float:
    """Probability ke user ko jawab bura laga (ground truth jo simulation chhupa rahi hai)."""
    base = {"faq_returns": 0.04, "faq_delivery": 0.05, "order_status": 0.06, "warranty": 0.06,
            "complaint": 0.25, "unknown": 0.30}[intent]
    if version == "v1.5" and intent == "faq_delivery":
        base = 0.32      # "max 25 words" -> city-wise delivery info cut ho gayi (regression!)
    if version == "v1.5" and intent == "unknown":
        base *= 0.8      # reranker ne unknown ko thora behtar kiya (improvement)
    if level == "fallback":
        base += 0.12     # fallback model Roman Urdu mein kamzor
    return min(base, 0.95)


def simulate(tr: Tracer, seed: int = 11) -> None:
    rng = random.Random(seed)
    names = list(INTENTS)
    weights = [INTENTS[i][0] for i in names]
    t0 = 1_790_000_000.0   # fixed start time (reproducible)
    for day in range(1, 15):
        version = "v1.4" if day < 8 else "v1.5"
        prompt_v = "support-v3" if day < 8 else "support-v4"
        retr = "hybrid-k3" if day < 8 else "hybrid-k3-rerank"
        for i in range(rng.randint(55, 70)):
            intent = rng.choices(names, weights)[0]
            _, examples, rids = INTENTS[intent]
            q = rng.choice(examples)
            phone = f"03{rng.randint(0, 9)}{rng.randint(10_000_000, 99_999_999)}"
            outage = day == 11 and 20 <= i < 32
            level = "fallback" if outage else "primary"
            cache = "exact" if intent.startswith("faq") and rng.random() < 0.25 else "none"
            if cache != "none":
                lat, tin, tout = rng.uniform(5, 40), 0, 0
            else:
                lat = rng.lognormvariate(7.15, 0.35)                 # ~1.3s median
                lat += 180 if retr.endswith("rerank") and rids else 0
                lat += 900 if level == "fallback" else 0
                tin, tout = rng.randint(1800, 3200), rng.randint(150, 420)
            rec = TraceRecord(
                input=q, output=f"(answer to: {q})", tenant="tussles_demo",
                user_hash=hash_user(phone), session_id=f"s{day}_{i}", intent=intent,
                route="tool->llm" if intent == "order_status" else
                      ("human" if intent == "complaint" else "rag->llm"),
                level=level, app_version=version, prompt_version=prompt_v,
                model="groq/gpt-oss-20b", served_by="ollama/local" if outage else "groq/gpt-oss-20b",
                retrieval_config=retr, kb_version=3, latency_ms=lat, ttft_ms=lat * 0.3,
                tokens_in=tin, tokens_out=tout, cost_usd=tin * PRICE_IN + tout * PRICE_OUT,
                cache_hit=cache, retrieved_ids=rids,
                tool_calls=["get_order_status"] if intent == "order_status" else [],
                ts=t0 + day * 86400 + i * 600, day=day)
            tid = tr.log(rec)

            bad = rng.random() < p_bad(intent, version, level)
            # Explicit feedback: sirf ~15% users thumbs dete hain (aksar naraz log zyada)
            if rng.random() < (0.35 if bad else 0.10):
                tr.feedback(tid, "explicit", "thumbs", -1 if bad else +1, ts=rec.ts + 60)
            # Implicit signals: kahin zyada data, lekin noisy
            if bad:
                sig = rng.choices(["rephrase", "asked_human", "abandoned"], [5, 3, 2])[0]
                tr.feedback(tid, "implicit", sig, -1, ts=rec.ts + 90)
            elif rng.random() < 0.5:
                tr.feedback(tid, "implicit", "resolved", +1, ts=rec.ts + 300)
    tr.commit()


# --------------------------------------------------------------------------
# Analysis
# --------------------------------------------------------------------------


def p95(vals: list[float]) -> float:
    if not vals:
        return 0.0
    s = sorted(vals)
    return s[int(0.95 * (len(s) - 1))]


def metrics(tr: Tracer, where: str = "1=1", params: tuple = ()) -> dict:
    rows = tr.query(f"SELECT trace_id, latency_ms, cost_usd, level, cache_hit FROM traces "
                    f"WHERE {where}", params)
    if not rows:
        return {}
    ids = [r[0] for r in rows]
    ph = ",".join("?" * len(ids))
    fb = tr.query(f"SELECT trace_id, kind, signal, value FROM feedback WHERE trace_id IN ({ph})",
                  tuple(ids))
    thumbs = [v for _, k, s, v in fb if s == "thumbs"]
    implicit_bad = {t for t, k, s, v in fb if k == "implicit" and v < 0}
    return {
        "n": len(rows),
        "p95": p95([r[1] for r in rows]),
        "cost_req": statistics.mean(r[2] for r in rows),
        "thumbs_n": len(thumbs),
        "thumbs_down": (sum(1 for v in thumbs if v < 0) / len(thumbs)) if thumbs else 0.0,
        "implicit_bad": len(implicit_bad) / len(rows),
        "fallback": sum(r[3] == "fallback" for r in rows) / len(rows),
        "cache": sum(r[4] != "none" for r in rows) / len(rows),
    }


def fmt_row(label: str, m: dict) -> str:
    return (f"  {label:<14}{m['n']:>5}{m['p95']:>8.0f}{m['cost_req'] * 1000:>9.3f}"
            f"{m['thumbs_down']:>9.0%}{m['implicit_bad']:>10.0%}{m['fallback']:>9.0%}"
            f"{m['cache']:>8.0%}")


HEADER = (f"  {'':<14}{'reqs':>5}{'p95ms':>8}{'m$/req':>9}{'👎rate':>9}{'implicit':>10}"
          f"{'fallbk':>9}{'cache':>8}")


def dashboard(tr: Tracer) -> dict[int, dict]:
    print("\n=== 2) DAILY DASHBOARD ===")
    print(HEADER)
    daily = {}
    for (day,) in tr.query("SELECT DISTINCT day FROM traces ORDER BY day"):
        m = metrics(tr, "day=?", (day,))
        daily[day] = m
        ver = tr.query("SELECT app_version FROM traces WHERE day=? LIMIT 1", (day,))[0][0]
        print(fmt_row(f"day {day:>2} {ver}", m))
    print("  (👎rate = explicit thumbs-down / thumbs given; implicit = rephrase/asked_human/abandoned)")
    print("  Dekho: 👎rate 0% se 57% tak uchhal raha hai, kyunke roz sirf ~9 log thumbs dete hain.")
    print("  Explicit feedback KAM aur NOISY hota hai; implicit signals zyada data dete hain.")
    return daily


def compare_versions(tr: Tracer) -> None:
    print("\n=== 3a) VERSION COMPARISON ===")
    print(HEADER)
    for (v,) in tr.query("SELECT DISTINCT app_version FROM traces ORDER BY app_version"):
        print(fmt_row(v, metrics(tr, "app_version=? AND level='primary'", (v,))))
    print("  Bad-rate badha (9% -> 15%), lekin KAHAN? Average mein masla chhup jata hai. Intent se todo:")

    print("\n=== 3b) VERSION x INTENT (implicit bad rate, primary traffic only) ===")
    intents = [r[0] for r in tr.query("SELECT DISTINCT intent FROM traces ORDER BY intent")]
    versions = [r[0] for r in tr.query("SELECT DISTINCT app_version FROM traces ORDER BY app_version")]
    print(f"  {'intent':<14}" + "".join(f"{v:>9}" for v in versions) + "   change")
    for it in intents:
        vals = [metrics(tr, "app_version=? AND intent=? AND level='primary'", (v, it))["implicit_bad"]
                for v in versions]
        delta = vals[-1] - vals[0]
        flag = "  ⚠️ REGRESSION" if delta > 0.10 else ("  ✅ better" if delta < -0.03 else "")
        print(f"  {it:<14}" + "".join(f"{x:>9.0%}" for x in vals) + f"   {delta:+.0%}{flag}")


def alerts(daily: dict[int, dict]) -> None:
    print("\n=== 4) ALERTS (rule-based, vs 7-day baseline) ===")
    days = sorted(daily)
    fired = 0
    for d in days[7:]:
        base = [daily[x] for x in days[max(0, d - 8):d - 1]]
        b_bad = statistics.mean(m["implicit_bad"] for m in base)
        b_cost = statistics.mean(m["cost_req"] for m in base)
        m = daily[d]
        msgs = []
        if m["implicit_bad"] > max(1.5 * b_bad, b_bad + 0.05):
            msgs.append(f"bad-rate {m['implicit_bad']:.0%} vs baseline {b_bad:.0%}")
        if m["p95"] > SLO_P95_MS:
            msgs.append(f"p95 {m['p95']:.0f}ms > SLO {SLO_P95_MS}ms")
        if m["fallback"] > 0.10:
            msgs.append(f"fallback traffic {m['fallback']:.0%} > 10%")
        if m["cost_req"] > 1.3 * b_cost:
            msgs.append(f"cost/req +{m['cost_req'] / b_cost - 1:.0%}")
        for msg in msgs:
            fired += 1
            print(f"  🚨 day {d}: {msg}")
    if not fired:
        print("  (koi alert nahi)")


def triage(tr: Tracer, n: int = 6) -> None:
    print("\n=== 5) TRIAGE: top failing inputs (negative feedback) ===")
    rows = tr.query("""
        SELECT t.input, t.intent, t.app_version, t.prompt_version, t.level, COUNT(*) c
        FROM traces t JOIN feedback f ON f.trace_id = t.trace_id
        WHERE f.value < 0 GROUP BY t.input, t.app_version, t.level ORDER BY c DESC LIMIT ?""", (n,))
    for inp, intent, ver, pv, level, c in rows:
        print(f"  {c:>3}x  {inp!r:36} intent={intent:<13} {ver}/{pv} level={level}")


def export_eval_candidates(tr: Tracer) -> None:
    print("\n=== 6) EXPORT: failures -> eval candidates ===")
    rows = tr.query("""
        SELECT t.trace_id, t.input, t.output, t.intent, t.app_version, t.prompt_version,
               t.model, t.served_by, t.retrieval_config, t.retrieved_ids,
               GROUP_CONCAT(DISTINCT f.signal)
        FROM traces t JOIN feedback f ON f.trace_id = t.trace_id
        WHERE f.value < 0 GROUP BY t.trace_id""")
    seen, items = set(), []
    for tid, inp, out, intent, ver, pv, model, served, retr, rids, sigs in rows:
        key = re.sub(r"\W+", " ", inp.lower()).strip()
        if key in seen:                  # dedupe: same sawal ek dafa
            continue
        seen.add(key)
        items.append({
            "input": inp,
            "actual_output": out,
            "expected_output": "",          # 👈 HUMAN bharega (sahi jawab kya hona chahiye tha)
            "context": json.loads(rids),
            "additional_metadata": {"source_trace_id": tid, "intent": intent, "app_version": ver,
                                    "prompt_version": pv, "model": model, "served_by": served,
                                    "retrieval_config": retr, "signals": sigs},
        })
    OUT.mkdir(exist_ok=True)
    (OUT / "eval_candidates.json").write_text(json.dumps(items, indent=2, ensure_ascii=False),
                                              encoding="utf-8")
    with open(OUT / "label_me.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["input", "intent", "app_version", "signals", "expected_output (fill me)"])
        for it in items:
            m = it["additional_metadata"]
            w.writerow([it["input"], m["intent"], m["app_version"], m["signals"], ""])
    print(f"  {len(items)} unique failing inputs -> {OUT / 'eval_candidates.json'}")
    print(f"  Labeling sheet -> {OUT / 'label_me.csv'}  (Excel mein kholo, expected_output bharo)")
    print("  Phir ye Level 7 DeepEval goldens / RAGAS dataset mein jate hain -> har naye deploy se")
    print("  PEHLE in par eval chalao (regression test). Yahi 'failures become eval cases' hai.")


def main() -> None:
    OUT.mkdir(exist_ok=True)
    db = OUT / "traces.db"
    if db.exists():
        db.unlink()
    tr = Tracer(db)
    print("=== 1) SIMULATE 14 days of production ===")
    simulate(tr)
    n = tr.query("SELECT COUNT(*) FROM traces")[0][0]
    nf = tr.query("SELECT COUNT(*) FROM feedback")[0][0]
    ne = tr.query("SELECT COUNT(*) FROM feedback WHERE kind='explicit'")[0][0]
    print(f"  {n} traces, {nf} feedback signals ({ne} explicit thumbs = {ne / n:.0%} of requests)")

    daily = dashboard(tr)
    compare_versions(tr)
    alerts(daily)
    triage(tr)
    export_eval_candidates(tr)

    print("\n=== 7) DECISION (on-call engineer ki tarah) ===")
    print("  - v1.5 ne faq_delivery bigara (prompt support-v4 'max 25 words' city info kaat raha hai).")
    print("  - Action: prompt_version ko support-v3 par ROLLBACK (sirf prompt; reranker rakh lo,")
    print("    kyunke unknown intent behtar hua). Versioning ki wajah se ye ek config change hai.")
    print("  - Failing delivery questions ko eval set mein daalo, support-v5 banao, eval pass ho to deploy.")
    print("  - Day 11 outage: fallback traffic ka bad-rate zyada tha -> fallback model ko Roman Urdu")
    print("    eval par test karo (M9.3).")


if __name__ == "__main__":
    main()
