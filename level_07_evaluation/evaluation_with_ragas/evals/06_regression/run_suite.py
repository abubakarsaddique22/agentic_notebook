"""
REGRESSION -- 1. RUN SUITE
==========================

Har change (prompt, model, chunk size, top_k) ke baad sawal: kya kuch TOOTA?
Ye script:
    1. chuni hui evals chalati ha (har eval apni CSV experiments/ ma likhti ha)
    2. har eval ki LATEST CSV se metric averages nikalti ha
    3. poora config (models, prompt ka hash, retriever settings, git commit) saath save
       karti ha -> regression/runs/<timestamp>.json   (VERSIONING: kis config pe kya score)
    4. compare.py se baseline ke against check -> koi metric gira to exit code 1
       (CI/CD quality gate: GitHub Actions isi exit code pe merge rok deta ha)

Run (project root se):
    python -m evals.06_regression.run_suite                      # default "core" suite
    python -m evals.06_regression.run_suite --suite all          # sab kuch (lamba)
    python -m evals.06_regression.run_suite --only retriever generator
    python -m evals.06_regression.run_suite --no-run             # evals dobara mat chalao,
                                                                 # latest CSVs se summary
    python -m evals.06_regression.run_suite --set-baseline       # is run ko naya baseline bana do
"""

import argparse
import glob
import hashlib
import importlib
import json
import math
import os
import subprocess
import sys
from datetime import datetime

import pandas as pd

RUNS_DIR = "regression/runs"
BASELINE_PATH = "regression/baseline.json"

# name -> (module, csv prefix, {metric: aggregation})
#   "mean"  = average (zyada behtar)
#   "p95"   = 95th percentile (kam behtar -- latency)
#   "rate"  = 1/0 column ka average (pass rate)
EVALS = {
    "retriever":   ("evals.01_component_level.eval_retriever", "retriever",
                    {"context_recall": "mean", "context_precision": "mean"}),
    "generator":   ("evals.01_component_level.eval_generator", "generator",
                    {"faithfulness": "mean", "answer_relevancy": "mean"}),
    "pipeline":    ("evals.02_pipeline.eval_rag_pipeline", "pipeline",
                    {"context_relevance": "mean", "faithfulness": "mean", "answer_relevancy": "mean"}),
    "application": ("evals.03_application.eval_application", "application",
                    {"answer_accuracy": "mean", "completeness": "mean", "teaching_style": "rate"}),
    "citation":    ("evals.03_application.eval_citation", "citation",
                    {"citation_present": "rate", "citation_valid": "mean", "citation_support": "rate"}),
    "toxicity":    ("evals.04_safety.eval_toxicity", "toxicity", {"safety_pass": "rate"}),
    "leakage":     ("evals.04_safety.eval_leakage", "leakage", {"leak_pass": "rate"}),
    "scope":       ("evals.04_safety.eval_scope", "scope", {"scope_pass": "rate"}),
    "injection":   ("evals.04_safety.eval_indirect_injection", "injection", {"injection_pass": "rate"}),
    "ops":         ("evals.05_operations.eval_ops", "ops",
                    {"latency_s": "p95", "ttft_s": "p95"}),
    "agent":       ("evals.08_agent.eval_agent", "agent",
                    {"tool_call_f1": "mean", "goal_accuracy": "rate", "end_state_pass": "rate",
                     "no_denied_tools": "rate"}),
}

SUITES = {
    "core":   ["retriever", "generator", "pipeline", "application"],
    "safety": ["toxicity", "leakage", "scope", "injection"],
    "all":    list(EVALS),
}


# ---------------------------------------------------------
# config fingerprint -- "ye score KIS setup ka ha?"
# ---------------------------------------------------------
def config_snapshot() -> dict:
    from dotenv import load_dotenv
    load_dotenv()
    snap = {
        "generator_model": os.getenv("GENERATOR_MODEL", "gpt-oss:20b-cloud"),
        "judge_model": os.getenv("JUDGE_MODEL", "gpt-oss:20b-cloud"),
        "judge_embed_model": os.getenv("OLLAMA_EMBED_MODEL", "all-minilm:latest"),
        "rag_embed": f"{os.getenv('RAG_EMBED_PROVIDER', 'ollama')}:{os.getenv('RAG_EMBED_MODEL', 'nomic-embed-text')}",
        "retriever": "chroma + ms-marco-MiniLM rerank, chunk 1000/150",
    }
    try:
        with open("src/generator.py", encoding="utf-8") as f:
            snap["generator_py_hash"] = hashlib.sha256(f.read().encode()).hexdigest()[:12]
    except OSError:
        pass
    try:
        snap["git_commit"] = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, check=True
        ).stdout.strip()
    except Exception:
        snap["git_commit"] = None
    return snap


# ---------------------------------------------------------
# CSV -> metric numbers
# ---------------------------------------------------------
def latest_csv(prefix: str) -> str | None:
    files = sorted(glob.glob(f"experiments/{prefix}_*.csv"))
    return files[-1] if files else None


def aggregate(values: list[float], how: str) -> float:
    vals = sorted(v for v in values if not math.isnan(v))
    if not vals:
        return float("nan")
    if how == "p95":
        return vals[min(len(vals) - 1, int(round(0.95 * (len(vals) - 1))))]
    return sum(vals) / len(vals)


def summarize(name: str) -> dict | None:
    _, prefix, metrics = EVALS[name]
    path = latest_csv(prefix)
    if not path:
        print(f"  [{name}] koi CSV nahi mili (experiments/{prefix}_*.csv)")
        return None
    df = pd.read_csv(path)
    out = {"csv": path, "n": len(df), "metrics": {}}
    for col, how in metrics.items():
        if col not in df.columns:
            continue
        values = pd.to_numeric(df[col], errors="coerce").astype(float).tolist()
        out["metrics"][col] = {
            "value": aggregate(values, how),
            "how": how,
            "errors": sum(math.isnan(v) for v in values),
        }
    return out


def run_eval(name: str) -> bool:
    module = EVALS[name][0]
    print(f"\n>>> RUN {name}: python -m {module}")
    proc = subprocess.run([sys.executable, "-m", module])
    if proc.returncode != 0:
        print(f"!!! {name} crash hua (exit {proc.returncode})")
        return False
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--suite", default="core", choices=list(SUITES))
    ap.add_argument("--only", nargs="*", choices=list(EVALS))
    ap.add_argument("--no-run", action="store_true", help="evals mat chalao, latest CSVs use karo")
    ap.add_argument("--set-baseline", action="store_true")
    ap.add_argument("--tolerance", type=float, default=0.05)
    args = ap.parse_args()

    names = args.only or SUITES[args.suite]
    crashed = []

    if not args.no_run:
        for name in names:
            if not run_eval(name):
                crashed.append(name)

    report = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "config": config_snapshot(),
        "evals": {},
        "crashed": crashed,
    }
    for name in names:
        s = summarize(name)
        if s:
            report["evals"][name] = s

    os.makedirs(RUNS_DIR, exist_ok=True)
    run_path = os.path.join(RUNS_DIR, f"{datetime.now():%Y%m%d-%H%M%S}.json")
    with open(run_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"\nRun saved: {run_path}")

    if args.set_baseline:
        os.makedirs(os.path.dirname(BASELINE_PATH), exist_ok=True)
        with open(BASELINE_PATH, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        print(f"Baseline set: {BASELINE_PATH}")
        sys.exit(1 if crashed else 0)

    # quality gate (folder naam "06_..." digit se shuru -> normal import nahi, importlib)
    compare = importlib.import_module("evals.06_regression.compare")
    sys.exit(compare.compare_reports(BASELINE_PATH, run_path, args.tolerance, crashed))


if __name__ == "__main__":
    main()
