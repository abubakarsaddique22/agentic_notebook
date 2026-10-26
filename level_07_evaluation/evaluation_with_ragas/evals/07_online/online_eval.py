"""
ONLINE -- 2. ONLINE EVAL PIPELINE (RAGAS)
=========================================

Flow (notes wala):  LOG -> SAMPLE -> EVALUATE -> AGGREGATE (dashboard) -> ALERT
                                                          \\-> failures wapas OFFLINE dataset ma

1. LOG        online/logs/traffic.jsonl  (simulate_traffic.py likhta ha)
2. SAMPLE     har conversation judge karna mehnga ha -> STRATIFIED sampling:
                 thumbs_down  100%   (user khud keh raha ha kuch ghalat ha)
                 abstained    100%   (kahin bot ne sahi sawal pe to mana nahi kiya?)
                 slow          50%   (p90 se zyada latency)
                 normal        30%
              Random sampling ma problem wali conversations aksar miss ho jati hain.
3. EVALUATE   golden answer nahi -> sirf REFERENCE-FREE RAGAS metrics:
                 Faithfulness      -- hallucination pakadne ke liye
                 AnswerRelevancy   -- sawal ka jawab diya?
                 ContextRelevance  -- sirf abstained pe: context relevant tha phir bhi mana kiya
                                      = "wrongful abstain"
4. AGGREGATE  captured (thumbs down rate, abstain rate, p95 latency, errors)
              + computed (avg faithfulness, hallucination rate, relevancy)
5. ALERT      threshold cross hua -> ALERT print (asli system ma Slack/email)
6. FEEDBACK   fail hui conversations -> goldens/online_candidates.json
              (status "needs_review": insaan ideal answer likh kar golden set ma daale --
               "self-improving golden dataset")

Run:  python -m evals.07_online.online_eval
      python -m evals.07_online.online_eval --last 50     # sirf aakhri 50 conversations
"""

import argparse
import asyncio
import json
import math
import os
import random
from collections import Counter
from datetime import datetime

from dotenv import load_dotenv

from ragas import experiment
# ---------------------------------------------------------
# experiment  (decorator)  -- RAGAS ka "run button" (DeepEval ke evaluate() jaisa)
#   @experiment() ek async function pe lagta ha jo EK row (dict) leta ha aur
#   result ka dict wapas karta ha. Decorator us function ko ExperimentWrapper
#   bana deta ha, jis pe .arun() milta ha.
#
#   @experiment(...) ke arguments (sab optional):
#     experiment_model -> pydantic model: har result row isi shape ma validate ho
#     backend          -> results kahan save hon (warna dataset wala backend)
#     name_prefix      -> har experiment naam ke aage lagne wala prefix
#
#   await my_experiment.arun(dataset, name="..."):
#     - dataset ki HAR row pe function chalata ha -- sab rows EK SAATH (asyncio).
#       RAGAS khud koi concurrency limit nahi lagata, isi liye hum apna
#       asyncio.Semaphore (_slots) use karte hain, warna Ollama pe 429 aata ha.
#     - koi row crash ho to "Warning: Task failed with error" print, row result
#       se GAYAB (is liye kuch files row ke andar try/except lagati hain)
#     - results experiments/<name>.csv ma save (local/csv backend)
#     - return: Experiment object -> .to_pandas() se DataFrame
#   NOTE: DeepEval ki tarah threshold / pass-fail RAGAS nahi lagata -- wo hum
#   khud harness.print_summary() ma THRESHOLD se karte hain.
# ---------------------------------------------------------
from ragas.metrics.collections import AnswerRelevancy, ContextRelevance, Faithfulness
# ---------------------------------------------------------
# ragas.metrics.collections  (RAGAS 0.4 ke naye "modern" metrics)
#   Sab ka pattern ek jaisa:
#     metric = SomeMetric(llm=judge_llm, ...)          # judge CONSTRUCTOR ma
#     result = await metric.ascore(field1=..., ...)     # sirf zaroori fields
#     result.value  -> score (aksar 0.0 se 1.0, zyada = behtar)
#     result.reason -> wajah (har metric nahi deta)
#   harness.safe_score() yahi ascore() chalata ha aur error pe NaN deta ha.
#
# Faithfulness(llm)  -- hallucination check
#   ascore(user_input, response, retrieved_contexts)
#   Kaise: response ko chhote atomic statements ma todta ha, phir har statement
#          context ke against check (NLI): context se support hota ha ya nahi.
#   Score = supported statements / total statements
#   Low = model context se bahar ki baatein bana raha ha
#
# AnswerRelevancy(llm, embeddings, strictness=3)  -- on-topic check
#   ascore(user_input, response)   (context nahi chahiye)
#   Kaise: judge response se ULTA `strictness` (3) sawal banata ha ("ye jawab kis
#          sawal ka hoga?"), phir un sawalon ki asli sawal se cosine similarity
#          (embeddings se) nikal kar average. Gol-mol / "pata nahi" jawab = 0.
#   Is liye ise EMBEDDINGS bhi chahiye (judge.get_judge_embeddings).
#   Low = jawab sawal se hat kar ha
#
# ContextRelevance(llm, max_retries=5)  -- retrieved context kitna kaam ka
#   ascore(user_input, retrieved_contexts)   (reference nahi chahiye)
#   Kaise: DO judge prompts (NVIDIA dual-judge) har ek 0 / 1 / 2 rating deta ha
#          (relevant nahi / thora / poora). Dono ka average -> 0.0-1.0.
#   Low = retriever galat ya noisy chunks laa raha ha
#
# Online ma golden answer nahi hota -> sirf ye REFERENCE-FREE metrics chalte hain.
# ContextRelevance yahan sirf abstain wale cases pe: context acha tha phir bhi
# mana kiya = "wrongful abstain".
# ---------------------------------------------------------

from judge import get_judge_embeddings, get_judge_llm, judge_info
from harness import build_dataset, safe_score

load_dotenv()

LOG_PATH = "online/logs/traffic.jsonl"
REPORT_DIR = "online/reports"
CANDIDATES_PATH = "goldens/online_candidates.json"
THRESHOLD = 0.7
MAX_CONCURRENT = 2

SAMPLE_RATES = {"thumbs_down": 1.0, "abstained": 1.0, "slow": 0.5, "normal": 0.3}

ALERTS = {                                    # (metric, direction, limit)
    "thumbs_down_rate":   ("max", 0.25),
    "abstain_rate":       ("max", 0.30),
    "error_rate":         ("max", 0.05),
    "p95_latency_s":      ("max", 30.0),
    "avg_faithfulness":   ("min", 0.80),
    "hallucination_rate": ("max", 0.15),
    "avg_answer_relevancy": ("min", 0.70),
}

judge_llm = get_judge_llm()
faithfulness = Faithfulness(llm=judge_llm)    # claims vs context -- sirf LLM chahiye
answer_relevancy = AnswerRelevancy(llm=judge_llm, embeddings=get_judge_embeddings())    # LLM (ulte sawal) + embeddings (cosine)
context_relevance = ContextRelevance(llm=judge_llm)    # dual judge 0/1/2 -> 0..1
_slots = asyncio.Semaphore(MAX_CONCURRENT)


# ---------------------------------------------------------
# 1-2. LOAD + STRATIFIED SAMPLE
# ---------------------------------------------------------
def load_logs(last: int | None) -> list[dict]:
    with open(LOG_PATH, encoding="utf-8") as f:
        logs = [json.loads(line) for line in f if line.strip()]
    return logs[-last:] if last else logs


def pct(values, p):
    values = sorted(values)
    return values[min(len(values) - 1, int(round(p / 100 * (len(values) - 1))))] if values else float("nan")


def stratum(rec: dict, slow_cutoff: float) -> str:
    if rec["error"]:
        return "error"                       # judge ki zaroorat nahi -- crash already failure ha
    if rec["feedback"] == "down":
        return "thumbs_down"
    if rec["abstained"]:
        return "abstained"
    if rec["latency_s"] > slow_cutoff:
        return "slow"
    return "normal"


def stratified_sample(logs: list[dict], seed: int = 7) -> list[dict]:
    rng = random.Random(seed)
    slow_cutoff = pct([r["latency_s"] for r in logs if not r["error"]], 90)
    groups: dict[str, list[dict]] = {}
    for r in logs:
        groups.setdefault(stratum(r, slow_cutoff), []).append({**r, "stratum": stratum(r, slow_cutoff)})

    sample = []
    for name, members in groups.items():
        rate = SAMPLE_RATES.get(name, 0.0)
        if rate == 0 or not members:
            continue
        k = max(1, round(len(members) * rate))
        sample += rng.sample(members, k)
    print("STRATA:", {k: len(v) for k, v in groups.items()}, "-> sampled", len(sample))
    return sample


# ---------------------------------------------------------
# 3. EVALUATE (computed signals)
# ---------------------------------------------------------
@experiment()    # is function ko RAGAS experiment bana do (.arun milega)
async def online_experiment(row):
    contexts = json.loads(row["contexts"])
    nan = float("nan")
    faith = ar = cr = nan
    reasons = {}

    async with _slots:
        if row["abstained"] in (True, "True", "true"):
            # mana kiya -- kya context waqai bekaar tha?
            cr, reasons["cr"] = await safe_score(
                context_relevance, user_input=row["query"], retrieved_contexts=contexts)
        else:
            faith, reasons["faith"] = await safe_score(
                faithfulness, user_input=row["query"], response=row["answer"],
                retrieved_contexts=contexts)
            ar, reasons["ar"] = await safe_score(
                answer_relevancy, user_input=row["query"], response=row["answer"])

    wrongful_abstain = (not math.isnan(cr)) and cr >= 0.5
    failed = (
        (not math.isnan(faith) and faith < THRESHOLD)
        or (not math.isnan(ar) and ar < THRESHOLD)
        or wrongful_abstain
        or row["feedback"] == "down"
    )
    return {
        **row,
        "faithfulness": faith,
        "answer_relevancy": ar,
        "context_relevance": cr,
        "wrongful_abstain": wrongful_abstain,
        "failed": failed,
        "reasons": json.dumps(reasons, ensure_ascii=False),
        **judge_info(),
    }


# ---------------------------------------------------------
# 4-6. AGGREGATE, ALERT, FEEDBACK LOOP
# ---------------------------------------------------------
def _mean(vals):
    vals = [v for v in vals if not math.isnan(v)]
    return sum(vals) / len(vals) if vals else float("nan")


def aggregate(logs, df) -> dict:
    n = len(logs)
    faith = df["faithfulness"].astype(float).tolist()
    judged_faith = [v for v in faith if not math.isnan(v)]
    return {
        # captured (POORE traffic pe -- sasta ha)
        "conversations": n,
        "thumbs_down_rate": sum(r["feedback"] == "down" for r in logs) / n,
        "abstain_rate": sum(bool(r["abstained"]) for r in logs) / n,
        "error_rate": sum(bool(r["error"]) for r in logs) / n,
        "p95_latency_s": pct([r["latency_s"] for r in logs if not r["error"]], 95),
        # computed (sirf SAMPLE pe -- mehnga)
        "judged": len(df),
        "avg_faithfulness": _mean(faith),
        "hallucination_rate": (sum(v < THRESHOLD for v in judged_faith) / len(judged_faith)
                               if judged_faith else float("nan")),
        "avg_answer_relevancy": _mean(df["answer_relevancy"].astype(float).tolist()),
        "wrongful_abstains": int(df["wrongful_abstain"].astype(str).eq("True").sum()),
    }


def check_alerts(stats: dict) -> list[str]:
    fired = []
    for key, (direction, limit) in ALERTS.items():
        v = stats.get(key)
        if v is None or (isinstance(v, float) and math.isnan(v)):
            continue
        if (direction == "max" and v > limit) or (direction == "min" and v < limit):
            fired.append(f"{key} = {v:.3f} ({'>' if direction == 'max' else '<'} {limit})")
    return fired


def feed_back_failures(df) -> int:
    existing = []
    if os.path.exists(CANDIDATES_PATH):
        with open(CANDIDATES_PATH, encoding="utf-8") as f:
            existing = json.load(f)
    seen = {c["query"] for c in existing}
    added = 0
    for _, r in df[df["failed"].astype(str) == "True"].iterrows():
        if r["query"] in seen:
            continue
        existing.append({
            "id": f"online_{r['conversation_id']}",
            "query": r["query"],
            "bad_answer": r["answer"],
            "why": {"stratum": r["stratum"], "faithfulness": r["faithfulness"],
                    "answer_relevancy": r["answer_relevancy"],
                    "wrongful_abstain": bool(r["wrongful_abstain"])},
            "ideal_answer": "",                 # insaan likhega
            "status": "needs_review",
        })
        seen.add(r["query"])
        added += 1
    with open(CANDIDATES_PATH, "w", encoding="utf-8") as f:
        json.dump(existing, f, indent=2, ensure_ascii=False, default=str)
    return added


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--last", type=int, default=None)
    args = ap.parse_args()

    logs = load_logs(args.last)
    if not logs:
        print(f"Log khali ha. Pehle: python -m evals.07_online.simulate_traffic")
        return
    sample = stratified_sample(logs)

    rows = [{k: (json.dumps(v, ensure_ascii=False) if k == "contexts" else v) for k, v in r.items()}
            for r in sample]
    dataset = build_dataset("online_sample", rows)

    run_name = f"online_{datetime.now():%Y%m%d-%H%M%S}"
    results = await online_experiment.arun(dataset, name=run_name)    # har row pe chalao -> experiments/<run_name>.csv
    df = results.to_pandas()    # Experiment -> pandas DataFrame

    stats = aggregate(logs, df)
    print("\n" + "=" * 60)
    print("ONLINE DASHBOARD")
    print("=" * 60)
    for k, v in stats.items():
        print(f"  {k:<22} {v:.3f}" if isinstance(v, float) else f"  {k:<22} {v}")
    print("\n  failures by stratum:", dict(Counter(df[df["failed"].astype(str) == "True"]["stratum"])))

    fired = check_alerts(stats)
    print("\nALERTS:" if fired else "\nALERTS: none")
    for a in fired:
        print(f"  !!! {a}")

    added = feed_back_failures(df)
    print(f"\nFEEDBACK LOOP: {added} nayi failing queries -> {CANDIDATES_PATH} (review kar ke golden ma daalo)")

    os.makedirs(REPORT_DIR, exist_ok=True)
    report_path = os.path.join(REPORT_DIR, f"{run_name}.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump({"stats": stats, "alerts": fired}, f, indent=2)
    print(f"Report: {report_path}   Detail: experiments/{run_name}.csv")


if __name__ == "__main__":
    asyncio.run(main())
