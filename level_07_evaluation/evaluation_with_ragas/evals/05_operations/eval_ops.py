"""
OPERATIONS -- latency, TTFT, tokens/cost, errors, consistency
=============================================================

Quality acchi ho lekin answer 40 second ma aaye, ya har query $0.05 ki ho, ya 10 ma
se 2 dafa crash ho -- to bhi app production ke qabil nahi. Ye "captured" signals hain:
inhe LLM judge nahi chahiye, bas NAAPNA ha.

Har query pe:
    retrieve_s    -- retriever + reranker ka time
    ttft_s        -- time to first token (user ko pehla lafz kab dikha -- streaming UX)
    generate_s    -- poora answer banne ka time
    latency_s     -- total (retrieve + generate)
    input/output_tokens -- Ollama ka asli usage (andaza nahi)
    cost_usd      -- tokens x price (.env: PRICE_IN_PER_1M / PRICE_OUT_PER_1M, default 0)
    error         -- pipeline crash hua?

Consistency (reliability) -- RAGAS SemanticSimilarity:
    pehli CONSISTENCY_N queries pe SAME context ke saath generator 3 dafa chalao,
    answers ki aapas ma embedding similarity. Kam = har dafa alag jawab (unpredictable).

Averages nahi, PERCENTILES: p95 = "20 ma se 1 user ka tajurba". SLOs neeche set hain.

Run:  python -m evals.05_operations.eval_ops
"""

import asyncio
import itertools
import math
import os
import time
from datetime import datetime

from dotenv import load_dotenv

from src.rag_pipeline import RagPipeline
from src.generator import GENERATOR_MODEL, generate, llm as generator_llm, prompt as generator_prompt

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
from ragas.metrics.collections import SemanticSimilarity
# ---------------------------------------------------------
# ragas.metrics.collections  (RAGAS 0.4 ke naye "modern" metrics)
#   Sab ka pattern ek jaisa:
#     metric = SomeMetric(llm=judge_llm, ...)          # judge CONSTRUCTOR ma
#     result = await metric.ascore(field1=..., ...)     # sirf zaroori fields
#     result.value  -> score (aksar 0.0 se 1.0, zyada = behtar)
#     result.reason -> wajah (har metric nahi deta)
#   harness.safe_score() yahi ascore() chalata ha aur error pe NaN deta ha.
#
# SemanticSimilarity(embeddings, threshold=None)  -- do texts ka matlab kitna milta ha
#   ascore(reference, response)
#   Kaise: dono texts ki embeddings, phir cosine similarity. LLM judge NAHI --
#          sirf embeddings (sasta, tez, deterministic).
#   Yahan: same sawal + same context pe generator 3 dafa chala kar answers aapas
#          ma compare = CONSISTENCY. Kam score = har dafa alag jawab.
#   threshold diya ho to score 1/0 ban jata ha (yahan nahi diya -> raw 0..1).
# ---------------------------------------------------------

from judge import get_judge_embeddings, judge_info
from harness import build_dataset, load_goldens, safe_score

load_dotenv()

GOLDEN_PATH = "goldens/retriever_goldens.json"
MAX_CONCURRENT = 1          # latency naapni ha -> ek waqt ma ek query (warna queue time bhi gin jata)
CONSISTENCY_N = 3           # pehli 3 queries pe consistency check
CONSISTENCY_RUNS = 3

PRICE_IN = float(os.getenv("PRICE_IN_PER_1M", "0"))      # $ per 1M input tokens
PRICE_OUT = float(os.getenv("PRICE_OUT_PER_1M", "0"))    # $ per 1M output tokens

# SLOs (service level objectives) -- apni app ke hisaab se badlo
SLO = {
    "p95_latency_s": 30.0,
    "p95_ttft_s": 10.0,
    "error_rate": 0.0,
    "avg_consistency": 0.85,
}

rag = RagPipeline()
gen_chain = generator_prompt | generator_llm          # StrOutputParser NAHI -> usage_metadata milta ha
# poore answers (300+ words) compare hote hain -> all-minilm (~256 token limit) kaafi nahi,
# nomic-embed-text (8k context) use karo -- RAG wala model, pehle se pulled
similarity = SemanticSimilarity(embeddings=get_judge_embeddings(os.getenv("RAG_EMBED_MODEL", "nomic-embed-text")))
_slots = asyncio.Semaphore(MAX_CONCURRENT)


def _generate_streaming(query: str, contexts: list[str]) -> dict:
    """Ek hi generation ma TTFT, total time aur token usage teeno."""
    t0 = time.perf_counter()
    ttft, full = None, None
    for chunk in gen_chain.stream({"question": query, "context": "\n\n".join(contexts)}):
        if ttft is None and chunk.content:
            ttft = time.perf_counter() - t0
        full = chunk if full is None else full + chunk      # chunks jodne se usage bhi judta ha
    usage = (getattr(full, "usage_metadata", None) or {}) if full is not None else {}
    return {
        "answer": full.content if full is not None else "",
        "ttft_s": ttft if ttft is not None else float("nan"),
        "generate_s": time.perf_counter() - t0,
        "input_tokens": usage.get("input_tokens", 0),
        "output_tokens": usage.get("output_tokens", 0),
    }


async def _consistency(query: str, contexts: list[str], first_answer: str) -> float:
    answers = [first_answer]
    for _ in range(CONSISTENCY_RUNS - 1):
        answers.append(await asyncio.to_thread(generate, query, contexts))
    scores, errors = [], []
    for a, b in itertools.combinations(answers, 2):
        s, reason = await safe_score(similarity, reference=a, response=b)
        scores.append(s)
        if reason.startswith("ERROR"):
            errors.append(reason)
    if errors:
        print(f"  consistency error ({query[:40]}): {errors[0][:200]}")
    ok = [s for s in scores if not math.isnan(s)]
    return sum(ok) / len(ok) if ok else float("nan")


@experiment()    # is function ko RAGAS experiment bana do (.arun milega)
async def ops_experiment(row):
    async with _slots:
        t0 = time.perf_counter()
        try:
            docs = await asyncio.to_thread(rag.retriever.invoke, row["query"])
            retrieve_s = time.perf_counter() - t0
            contexts = [d.page_content for d in docs]

            gen = await asyncio.to_thread(_generate_streaming, row["query"], contexts)
            error = ""
        except Exception as e:
            retrieve_s, contexts = time.perf_counter() - t0, []
            gen = {"answer": "", "ttft_s": float("nan"), "generate_s": 0.0,
                   "input_tokens": 0, "output_tokens": 0}
            error = f"{type(e).__name__}: {e}"
        latency_s = time.perf_counter() - t0

        consistency = float("nan")
        if not error and int(row["order"]) < CONSISTENCY_N:
            consistency = await _consistency(row["query"], contexts, gen["answer"])

    cost = gen["input_tokens"] / 1e6 * PRICE_IN + gen["output_tokens"] / 1e6 * PRICE_OUT
    return {
        **row,
        "answer": gen["answer"],
        "retrieve_s": round(retrieve_s, 2),
        "ttft_s": round(gen["ttft_s"], 2),
        "generate_s": round(gen["generate_s"], 2),
        "latency_s": round(latency_s, 2),
        "input_tokens": gen["input_tokens"],
        "output_tokens": gen["output_tokens"],
        "cost_usd": round(cost, 6),
        "error": error,
        "consistency": consistency,
        "generator_model": GENERATOR_MODEL,
        **judge_info(),
    }


def pct(values, p):
    values = sorted(v for v in values if not math.isnan(v))
    if not values:
        return float("nan")
    return values[min(len(values) - 1, int(round(p / 100 * (len(values) - 1))))]


def report(df):
    n = len(df)
    errors = int((df["error"].fillna("") != "").sum())
    lat = df["latency_s"].astype(float).tolist()
    ttft = df["ttft_s"].astype(float).tolist()
    cons = [v for v in df["consistency"].astype(float).tolist() if not math.isnan(v)]
    tin, tout = df["input_tokens"].astype(float), df["output_tokens"].astype(float)
    cost = df["cost_usd"].astype(float)

    measured = {
        "p95_latency_s": pct(lat, 95),
        "p95_ttft_s": pct(ttft, 95),
        "error_rate": errors / n if n else float("nan"),
        "avg_consistency": sum(cons) / len(cons) if cons else float("nan"),
    }

    print("\n" + "=" * 60)
    print(f"OPERATIONS  ({n} queries)")
    print("=" * 60)
    for col in ["retrieve_s", "ttft_s", "generate_s", "latency_s"]:
        v = df[col].astype(float).tolist()
        print(f"{col:<12} p50 = {pct(v, 50):6.1f}s   p95 = {pct(v, 95):6.1f}s   max = {max(v):6.1f}s")
    print(f"\ntokens/query  input avg {tin.mean():.0f}   output avg {tout.mean():.0f}")
    print(f"cost          per query ${cost.mean():.5f}   per 1,000 queries ${cost.mean() * 1000:.2f}"
          + ("   (PRICE_IN/OUT_PER_1M .env ma set nahi -> 0)" if PRICE_IN == PRICE_OUT == 0 else ""))
    print(f"errors        {errors}/{n}")
    print(f"consistency   {measured['avg_consistency']:.3f}  (first {CONSISTENCY_N} queries x {CONSISTENCY_RUNS} runs)")

    print("\nSLO CHECK:")
    for key, limit in SLO.items():
        value = measured[key]
        good = value >= limit if key == "avg_consistency" else value <= limit
        mark = "PASS" if good else "FAIL"
        print(f"  {key:<16} {value:8.3f}   limit {limit:<6}  {mark}")


async def main():
    goldens = load_goldens(GOLDEN_PATH)
    print(f"Loaded {len(goldens)} queries from {GOLDEN_PATH}")

    rows = [{"id": g["id"], "query": g["query"], "order": i} for i, g in enumerate(goldens)]
    dataset = build_dataset("ops_queries", rows)

    run_name = f"ops_{datetime.now():%Y%m%d-%H%M%S}"
    results = await ops_experiment.arun(dataset, name=run_name)    # har row pe chalao -> experiments/<run_name>.csv

    report(results.to_pandas())
    print(f"\nPoori detail: experiments/{run_name}.csv")


if __name__ == "__main__":
    asyncio.run(main())
