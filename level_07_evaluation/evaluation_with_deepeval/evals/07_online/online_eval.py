"""
evals/07_online/online_eval.py
==============================
ONLINE EVAL (roadmap M7.3) -- production traces pe continuous evaluation.

Offline eval = deploy se PEHLE, golden set (answer key) ke saath.
Online eval  = deploy ke BAAD, asli traffic pe, BINA answer key ke.

Is liye online ma sirf REFERENCE-FREE metrics chalte hain:
    Faithfulness      answer retrieved context se supported ha?   (expected_output nahi chahiye)
    Answer Relevancy  answer sawal ka jawab deta ha?              (expected_output nahi chahiye)

Pipeline (har run pe):
    1. LOG       LangSmith se pichle LOOKBACK_HOURS ke RagPipeline traces lo
    2. SAMPLE    sab pe judge chalana mehenga ha -> SAMPLE_RATE % uthao
                 (jo runs pehle score ho chuke, unhe skip -- dobara paisa nahi)
    3. SYSTEM    captured signals: latency, error rate, tokens  (free, har trace pe)
    4. QUALITY   computed signals: DeepEval judge sirf sampled traces pe
    5. WRITE     scores wapas LangSmith feedback ma (UI ma trace ke saath dikhte hain)
    6. ALERT     threshold se neeche -> ALERT + exit code 2 (scheduler/cron pakar sake)
    7. DRIFT     production queries golden queries se kitni alag hain?
    8. FEEDBACK  fail hone wale cases -> goldens/candidates/online_failures.json
                 (insaan review kare, ideal_answer likhe, phir golden set ma daale
                  = SELF-IMPROVING GOLDEN DATASET)

Zaroori .env:
    LANGCHAIN_API_KEY=...
    LANGCHAIN_PROJECT=<project>   (optional, warna "default")

Run (project root se):
    python -m evals.07_online.simulate_traffic     # pehle kuch traffic banao
    python -m evals.07_online.online_eval
"""

print("[1] online_eval.py started")

# IMPORT ORDER (Windows): judge -> deepeval  (yahan src import nahi hota)
from judge import get_judge, JUDGE_MODEL
from programmatic import is_abstain
from harness import load_goldens

import json
import math
import os
import random
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from dotenv import load_dotenv
from langsmith import Client

from deepeval import evaluate
# ---------------------------------------------------------
# evaluate  (function)
#   DeepEval ka main "run button". Test cases + metrics leta ha, har test case
#   pe har metric chalata ha (judge LLM ko call karke), score + reason nikalta
#   ha, terminal pe table print karta ha, aur EvaluationResult wapas deta ha.
#   Arguments:
#     test_cases      -> LLMTestCase ki list (KYA check karna ha)
#     metrics         -> metric objects ki list (KIS cheez pe check karna ha)
#     async_config    -> AsyncConfig (parallel kitna chalana ha) -- optional
#     hyperparameters -> dict, sirf record/logging ke liye (model, top_k, waghera).
#                        Score pe asar NAHI, bas runs compare karne ke kaam aata ha.
#   Return: EvaluationResult -> .test_results (list). Har item ma:
#     .name, .input, .actual_output, .success, aur .metrics_data (list) jis ma
#     har metric ka .name, .score, .success, .reason hota ha.
# ---------------------------------------------------------
from deepeval.evaluate.configs import AsyncConfig
# ---------------------------------------------------------
# AsyncConfig  (settings class)
#   evaluate() ko batata ha ke test cases ko parallel (async) kaise chalaye.
#     run_async      -> True (default) = async, False = ek ek karke (sequential)
#     max_concurrent -> ek waqt ma kitne test cases saath chalein (default 20,
#                       Ollama ke liye zyada ha -- is liye 1 ya 2 rakhte hain)
#     throttle_value -> har test case se pehle kitne second ruko (default 0),
#                       rate limit (429) se bachne ke liye
#   Note: ye TEST CASE level ki limit ha. Ek test case ke andar metric kai judge
#   calls bhej sakta ha -- un ko judge.py ka semaphore control karta ha.
# ---------------------------------------------------------
from deepeval.test_case import LLMTestCase
# ---------------------------------------------------------
# LLMTestCase  (data container class)
#   Ek "test case" = ek sawal aur us se judi saari cheezen. Metrics isi object
#   se fields parhte hain. Khud koi kaam nahi karta, sirf data rakhta ha.
#   Attributes (jo is project ma use hote hain):
#     input               -> user ka sawal / message
#     actual_output       -> aap ke system ne jo jawab diya (yahi test hota ha)
#     expected_output     -> sahi / ideal jawab ya expected behaviour (golden se)
#     retrieval_context   -> wo chunks jo generator ko diye gaye (list of strings)
#     name                -> test case ka naam/id (report ma isi se pehchante hain)
#     additional_metadata -> apna extra data (dict). Metric score pe asar nahi,
#                            lekin hamare programmatic metrics isay parhte hain.
#                            (naye 4.x ma iska naya naam `metadata` ha)
#   Yahan: name = LangSmith run id (score wapas usi trace pe likhne ke liye),
#   input / actual_output / retrieval_context production trace se aate hain.
#   expected_output NAHI -- production ma answer key hoti hi nahi.
# ---------------------------------------------------------
from deepeval.metrics import FaithfulnessMetric, AnswerRelevancyMetric
# ---------------------------------------------------------
# FaithfulnessMetric  (generator metric -- hallucination check)
#   Sawal: "Kya jawab ki har baat diye gaye context se SABIT hoti ha?"
#   Kaise: judge actual_output se claims nikalta ha, retrieval_context se facts
#          nikalta ha, phir har claim check karta ha ke context use contradict
#          to nahi karta.
#   Score = (wo claims jo context ke khilaf nahi) / (total claims)  -> 0 se 1
#   Chahiye: input, actual_output, retrieval_context
#   Low score = model apni taraf se baatein bana raha ha (hallucination)
#
# AnswerRelevancyMetric  (generator metric -- on-topic check)
#   Sawal: "Kya jawab ASAL sawal ka hi jawab ha, ya idhar udhar ki baatein?"
#   Kaise: judge actual_output ko statements ma todta ha, har statement ko input
#          ke against relevant / irrelevant mark karta ha.
#   Score = (relevant statements) / (total statements)  -> 0 se 1
#   Chahiye: input, actual_output   (context ya expected_output nahi chahiye)
#   Low score = jawab off-topic ha ya sawal ko miss kar gaya
#
# Common attributes (constructor arguments):
#   threshold      -> pass/fail ki line
#   model          -> judge LLM (OllamaJudge). Na do to DeepEval default OpenAI model lega
#   include_reason -> True = score ke saath "kyun" bhi likhe
#   strict_mode    -> True = score sirf 0 ya 1
#   async_mode     -> (optional, default True) andar ki judge calls async
#   verbose_mode   -> (optional) andar ke steps print kare
# Run ke baad metric pe milte hain: .score, .reason, .success
#
# Dono REFERENCE-FREE hain (expected_output nahi chahiye) -- isi liye online
# eval (production traffic, jahan answer key nahi hoti) ma chal sakte hain.
# ---------------------------------------------------------

print("[2] deepeval imported")

load_dotenv()

# =========================================================
# CONFIG
# =========================================================
PROJECT = os.getenv("LANGCHAIN_PROJECT") or os.getenv("LANGSMITH_PROJECT") or "default"
RUN_NAME = "RagPipeline"          # src/rag_pipeline.py @traceable(name=...)
LOOKBACK_HOURS = 24
SAMPLE_RATE = 0.5                 # 50% traces judge honge
MAX_SAMPLES = 10                  # ek run ma zyada se zyada (judge cost control)
FETCH_LIMIT = 100                 # LangSmith API ki max limit 100 ha
RANDOM_SEED = None                # None = har dafa alag sample; number = reproducible
THRESHOLD = 0.7
MAX_CONCURRENT = 1
FEEDBACK_PREFIX = "online_"       # LangSmith feedback keys: online_faithfulness, ...

# ALERT thresholds
ALERTS = {
    "faithfulness_pass_rate_min": 80.0,     # %
    "relevancy_pass_rate_min": 80.0,        # %
    "abstain_rate_max": 30.0,               # % -- bohot zyada "I don't know" = retriever ya scope masla
    "error_rate_max": 5.0,                  # %
    "latency_p95_ms_max": 10000.0,
}

# DRIFT thresholds
DRIFT = {
    "novel_word_rate_max": 0.60,            # production words jo golden queries ma kabhi nahi aaye
    "length_ratio_range": (0.5, 2.0),       # avg query length production / golden
}

CANDIDATES_PATH = Path("goldens/candidates/online_failures.json")
REPORTS_DIR = Path("results/online")
GOLDEN_QUERY_FILES = [
    ("goldens/correctness_goldens.json", "question"),
    ("goldens/faithfulness_dataset.json", "query"),
    ("goldens/retriever_goldens.json", "query"),
]


# =========================================================
# 1. LOG: fetch traces
# =========================================================

def _io(run):
    """RagPipeline.invoke ke inputs/outputs se query, context, answer nikaalo."""
    inputs, outputs = run.inputs or {}, run.outputs or {}
    if "output" in outputs and isinstance(outputs["output"], dict):
        outputs = outputs["output"]
    query = outputs.get("query") or inputs.get("query") or next(
        (v for k, v in inputs.items() if isinstance(v, str)), ""
    )
    return query, outputs.get("context") or [], outputs.get("answer") or ""


def fetch_runs(client):
    since = datetime.now(timezone.utc) - timedelta(hours=LOOKBACK_HOURS)
    # LangSmith API ek request ma max 100 runs deti ha (limit > 100 = 400 Bad Request).
    # filter se sirf RagPipeline wale root runs mangwao, taake doosri traces (agent, evals)
    # 100 ki limit kha na jayen.
    runs = list(client.list_runs(
        project_name=PROJECT,
        is_root=True,
        start_time=since,
        filter=f'eq(name, "{RUN_NAME}")',
        limit=FETCH_LIMIT,
    ))
    print(f"Fetched {len(runs)} '{RUN_NAME}' traces from project '{PROJECT}' (last {LOOKBACK_HOURS}h)")
    return runs


def already_scored(run):
    stats = run.feedback_stats or {}
    return any(k.startswith(FEEDBACK_PREFIX) for k in stats)


# =========================================================
# 3. SYSTEM metrics (captured -- har trace pe, free)
# =========================================================

def percentile(values, p):
    if not values:
        return float("nan")
    s = sorted(values)
    k = (len(s) - 1) * p / 100
    lo, hi = math.floor(k), math.ceil(k)
    return s[lo] if lo == hi else s[lo] * (hi - k) + s[hi] * (k - lo)


def system_metrics(runs):
    latencies, errors, tokens, abstains = [], 0, [], 0
    for r in runs:
        if r.error:
            errors += 1
            continue
        if r.start_time and r.end_time:
            latencies.append((r.end_time - r.start_time).total_seconds() * 1000)
        if r.total_tokens:
            tokens.append(r.total_tokens)
        if is_abstain(_io(r)[2]):
            abstains += 1
    n = len(runs) or 1
    ok = len(runs) - errors or 1
    return {
        "traces": len(runs),
        "error_rate": 100 * errors / n,
        "abstain_rate": 100 * abstains / ok,
        "latency_p50_ms": percentile(latencies, 50),
        "latency_p95_ms": percentile(latencies, 95),
        "avg_total_tokens": (sum(tokens) / len(tokens)) if tokens else None,
    }


# =========================================================
# 7. DRIFT: production queries vs golden queries
# =========================================================

WORD_RE = re.compile(r"[a-z]+")


def _words(text):
    return WORD_RE.findall((text or "").lower())


def drift_check(prod_queries):
    golden_queries = []
    for path, field in GOLDEN_QUERY_FILES:
        if Path(path).exists():
            golden_queries += [g.get(field, "") for g in load_goldens(path)]

    vocab = {w for q in golden_queries for w in _words(q)}
    prod_words = [w for q in prod_queries for w in _words(q)]

    novel_rate = (sum(w not in vocab for w in prod_words) / len(prod_words)) if prod_words else 0.0
    avg_len = lambda qs: (sum(len(_words(q)) for q in qs) / len(qs)) if qs else 0.0
    ratio = (avg_len(prod_queries) / avg_len(golden_queries)) if golden_queries and avg_len(golden_queries) else float("nan")

    lo, hi = DRIFT["length_ratio_range"]
    flags = []
    if novel_rate > DRIFT["novel_word_rate_max"]:
        flags.append(f"novel_word_rate {novel_rate:.0%} > {DRIFT['novel_word_rate_max']:.0%} (users naye topics/zubaan use kar rahe hain)")
    if not (lo <= ratio <= hi):
        flags.append(f"query length ratio {ratio:.2f} outside [{lo}, {hi}]")

    novel_examples = sorted({w for w in prod_words if w not in vocab and len(w) > 3})[:15]
    return {"novel_word_rate": novel_rate, "length_ratio": ratio, "flags": flags, "novel_examples": novel_examples}


# =========================================================
# 8. FEEDBACK LOOP: failures -> golden candidates
# =========================================================

def save_candidates(failures):
    CANDIDATES_PATH.parent.mkdir(parents=True, exist_ok=True)
    existing = json.loads(CANDIDATES_PATH.read_text(encoding="utf-8")) if CANDIDATES_PATH.exists() else []
    seen = {c["run_id"] for c in existing}
    new = [f for f in failures if f["run_id"] not in seen]
    CANDIDATES_PATH.write_text(json.dumps(existing + new, indent=2, ensure_ascii=False), encoding="utf-8")
    return len(new), len(existing) + len(new)


# =========================================================
# MAIN
# =========================================================

def main():
    client = Client()
    runs = fetch_runs(client)
    if not runs:
        print("Koi trace nahi mila. Pehle traffic banao: python -m evals.07_online.simulate_traffic")
        print("Aur .env ma LANGCHAIN_TRACING_V2=true + LANGCHAIN_API_KEY check karo.")
        return 1

    # 3. SYSTEM metrics -- sab traces pe
    sys_m = system_metrics(runs)

    # 2. SAMPLE -- sirf successful, abhi tak unscored, answer wale traces
    rng = random.Random(RANDOM_SEED)
    pool = [r for r in runs if not r.error and not already_scored(r) and _io(r)[2]]
    sampled = [r for r in pool if rng.random() < SAMPLE_RATE][:MAX_SAMPLES]
    print(f"Sampling: {len(pool)} unscored traces -> {len(sampled)} judged (rate={SAMPLE_RATE:.0%}, max={MAX_SAMPLES})")

    quality = {}
    failures = []
    if sampled:
        # 4. QUALITY -- reference-free metrics
        test_cases = []
        for r in sampled:
            query, context, answer = _io(r)
            test_cases.append(LLMTestCase(
                name=str(r.id),                      # result ko wapas run se jorne ke liye
                input=query,    # sawal / user message
                actual_output=answer,    # bot ka jawab -- yahi test ho raha ha
                retrieval_context=[str(c) for c in context] or ["(no context)"],    # wo chunks jo generator ko diye gaye
            ))

        judge = get_judge()
        result = evaluate(
            test_cases=test_cases,    # kya check karna ha (LLMTestCase list)
            metrics=[    # kin metrics pe check karna ha
                FaithfulnessMetric(threshold=THRESHOLD, model=judge, include_reason=True),
                AnswerRelevancyMetric(threshold=THRESHOLD, model=judge, include_reason=True),
            ],
            async_config=AsyncConfig(max_concurrent=MAX_CONCURRENT),    # ek waqt ma MAX_CONCURRENT test cases
            hyperparameters={"eval": "online", "project": PROJECT, "judge_model": JUDGE_MODEL,    # sirf record ke liye -- score pe asar nahi
                             "sample_rate": SAMPLE_RATE},
        )

        by_name = {tc.name: tc for tc in test_cases}
        stats = {}
        for tr in result.test_results:
            failed = {}
            for m in tr.metrics_data or []:
                key = FEEDBACK_PREFIX + re.sub(r"[^a-z0-9]+", "_", m.name.lower()).strip("_")
                s = stats.setdefault(m.name, {"n": 0, "passed": 0, "scores": []})
                s["n"] += 1
                s["passed"] += bool(m.success)
                if m.score is not None:
                    s["scores"].append(m.score)
                    # 5. WRITE back to LangSmith
                    try:
                        client.create_feedback(tr.name, key=key, score=m.score, comment=(m.reason or "")[:500])
                    except Exception as e:
                        print(f"  feedback write failed for {tr.name}: {e}")
                if not m.success:
                    failed[m.name] = {"score": m.score, "reason": m.reason}

            if failed:
                tc = by_name[tr.name]
                failures.append({
                    "run_id": tr.name,
                    "query": tc.input,
                    "answer": tc.actual_output,
                    "failed_metrics": failed,
                    "captured_at": datetime.now().isoformat(timespec="seconds"),
                    "status": "needs_review",
                    "ideal_answer": "",          # insaan likhega
                })

        quality = {
            name: {"n": s["n"], "pass_rate": 100 * s["passed"] / s["n"],
                   "avg_score": (sum(s["scores"]) / len(s["scores"])) if s["scores"] else float("nan")}
            for name, s in stats.items()
        }

    # 7. DRIFT
    drift = drift_check([_io(r)[0] for r in runs if not r.error])

    # 6. ALERTS
    alerts = []
    for name, q in quality.items():
        lname = name.lower()
        if "faithfulness" in lname and q["pass_rate"] < ALERTS["faithfulness_pass_rate_min"]:
            alerts.append(f"Faithfulness pass rate {q['pass_rate']:.0f}% < {ALERTS['faithfulness_pass_rate_min']:.0f}%")
        if "relevancy" in lname and q["pass_rate"] < ALERTS["relevancy_pass_rate_min"]:
            alerts.append(f"Answer relevancy pass rate {q['pass_rate']:.0f}% < {ALERTS['relevancy_pass_rate_min']:.0f}%")
    if sys_m["abstain_rate"] > ALERTS["abstain_rate_max"]:
        alerts.append(f"Abstain rate {sys_m['abstain_rate']:.0f}% > {ALERTS['abstain_rate_max']:.0f}%")
    if sys_m["error_rate"] > ALERTS["error_rate_max"]:
        alerts.append(f"Error rate {sys_m['error_rate']:.1f}% > {ALERTS['error_rate_max']:.0f}%")
    p95 = sys_m["latency_p95_ms"]
    if p95 == p95 and p95 > ALERTS["latency_p95_ms_max"]:
        alerts.append(f"Latency p95 {p95:.0f}ms > {ALERTS['latency_p95_ms_max']:.0f}ms")
    alerts += [f"DRIFT: {f}" for f in drift["flags"]]

    # 8. FEEDBACK LOOP
    n_new, n_total = save_candidates(failures) if failures else (0, None)

    # REPORT
    print("\n" + "=" * 78)
    print(f"ONLINE EVAL REPORT   project={PROJECT}   window={LOOKBACK_HOURS}h")
    print("=" * 78)
    print("SYSTEM (captured, all traces):")
    for k, v in sys_m.items():
        print(f"  {k:<20} {v:.1f}" if isinstance(v, float) and v == v else f"  {k:<20} {v}")
    print("QUALITY (computed, sampled traces):")
    if quality:
        for name, q in quality.items():
            print(f"  {name:<28} pass_rate={q['pass_rate']:5.0f}%  avg={q['avg_score']:.2f}  n={q['n']}")
    else:
        print("  (nothing new to judge -- sab traces pehle score ho chuke)")
    print("DRIFT:")
    print(f"  novel_word_rate      {drift['novel_word_rate']:.0%}   e.g. {', '.join(drift['novel_examples'][:8])}")
    print(f"  length_ratio         {drift['length_ratio']:.2f}")
    print("-" * 78)
    if failures:
        print(f"FEEDBACK LOOP: {n_new} new failure(s) -> {CANDIDATES_PATH} (total {n_total}).")
        print("  Inhe review karo, ideal_answer likho, phir sahi golden file ma move karo.")
    if alerts:
        print("ALERTS:")
        for a in alerts:
            print(f"  !! {a}")
    else:
        print("ALERTS: none")
    print("=" * 78)

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORTS_DIR / f"{datetime.now():%Y-%m-%dT%H-%M-%S}.json"
    report_path.write_text(json.dumps({"project": PROJECT, "system": sys_m, "quality": quality, "drift": drift,
                                       "alerts": alerts, "new_failures": n_new}, indent=2, default=str),
                           encoding="utf-8")
    print(f"report -> {report_path}")
    return 2 if alerts else 0


if __name__ == "__main__":
    sys.exit(main())
