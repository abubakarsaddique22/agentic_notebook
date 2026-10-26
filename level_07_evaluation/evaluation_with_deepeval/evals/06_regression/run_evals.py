"""
evals/06_regression/run_evals.py
================================
REGRESSION SUITE -- step 1: saari evals chalao, EK snapshot banao.

Snapshot = ek JSON file jisme:
    metrics : {"pipeline.faithfulness.pass_rate": 90.0, "ops.latency.e2e_p95_ms": 2400, ...}
    config  : is run ka poora "version" -- generator model, prompt ka hash, judge,
              retriever settings, har golden file ka hash, deepeval version, git commit
    errors  : jo suite crash hui (gate isay FAIL maanta ha)

Kyun config bhi save karte hain: jab number gire, sab se pehla sawal hota ha
"is run ma BADLA kya tha?" -- compare.py baseline aur current ka config diff dikhata ha.

Files:
    results/runs/<run_id>.json   har run ki history (experiment tracking)
    results/latest.json          sab se naya run
    results/baseline.json        "known good" run (compare.py --promote se banta ha)

Run (project root se):
    python -m evals.06_regression.run_evals                         # sab suites
    python -m evals.06_regression.run_evals --suites citation,injection
    python -m evals.06_regression.run_evals --suites core --note "chunk_size 800"
    python -m evals.06_regression.run_evals --suites safety --gate  # run + baseline se compare, fail pe exit 1
    python -m evals.06_regression.run_evals --list
"""

print("[1] run_evals.py started")

# ---------------------------------------------------------
# IMPORT ORDER (Windows): src.* -> judge -> deepeval
# ---------------------------------------------------------
from src.rag_pipeline import RagPipeline

print("[2] pipeline imported")

import judge                              # shared Ollama judge (project root) -- deepeval timeouts bhi set karta ha
from harness import summarize_by_metric, flatten_summary

import argparse
import hashlib
import importlib
import json
import math
import platform
import subprocess
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

RESULTS_DIR = Path("results")
RUNS_DIR = RESULTS_DIR / "runs"
LATEST_PATH = RESULTS_DIR / "latest.json"
BASELINE_PATH = RESULTS_DIR / "baseline.json"
GOLDENS_DIR = Path("goldens")


# =========================================================
# SUITES
# =========================================================
# Har suite: (module path, function(module, rag) -> flat {key: value})
# Module LAZY import hota ha -- jo suite nahi chalani, wo load bhi nahi hoti.

def _summary(prefix):
    """run() jo per-metric summary deta ha usay flat banao."""
    return lambda summary: flatten_summary(prefix, summary)


def _prefixed(prefix):
    """run_safety()/run_ops() pehle se flat dict dete hain -- bas prefix lagao."""
    return lambda flat: {f"{prefix}.{k}": v for k, v in flat.items()}


SUITES = {
    # name         module                                        how to call                                   how to flatten
    "retriever":   ("evals.01_compounts_level.01_eval_retriever", lambda m, rag: m.run(rag.retriever),           _summary("retriever")),
    "generator":   ("evals.01_compounts_level.02_eval_generator", lambda m, rag: m.run(),                        _summary("generator")),
    "pipeline":    ("evals.02_pipeline.03_eval_rag_pipeline",     lambda m, rag: m.run(rag),                     _summary("pipeline")),
    "application": ("evals.03_application.eval_application",      lambda m, rag: m.run(rag),                     _summary("application")),
    "citation":    ("evals.03_application.eval_citation",         lambda m, rag: m.run(rag),                     _summary("citation")),
    "injection":   ("evals.04_security.eval_indirect_injection",  lambda m, rag: summarize_by_metric(m.run(rag)), _summary("injection")),
    "safety":      ("evals.04_security.eval_safety",              lambda m, rag: m.run_safety(rag),              _prefixed("safety")),
    "ops":         ("evals.05_operation.eval_ops",                lambda m, rag: m.run_ops(rag),                 _prefixed("ops")),
    "agent":       ("evals.08_agent.eval_agent",                  lambda m, rag: m.run(),                        _summary("agent")),
}

PRESETS = {
    "all":     list(SUITES),
    "core":    ["retriever", "generator", "pipeline", "application"],   # RAG quality
    "rag":     ["retriever", "generator", "pipeline", "application", "citation"],
    "safety":  ["safety", "injection"],
    "quick":   ["citation", "injection"],                                  # chote golden sets
}


# =========================================================
# CONFIG CAPTURE (versioning)
# =========================================================

def _sha(data) -> str:
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()[:12]


def _git_commit():
    try:
        out = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, timeout=5)
        return out.stdout.strip() or None
    except Exception:
        return None


def capture_config(rag, note):
    import src.generator as gen
    import src.reranker as reranker

    try:
        import deepeval
        # ---------------------------------------------------------
        # import deepeval  (poora package)
        #   Yahan koi class use nahi ho rahi -- sirf deepeval.__version__ parh rahe hain
        #   taake snapshot ke config ma likha jaye ke kaunsa DeepEval version tha.
        #   Kyun: naye version ma metric ka prompt/scoring badal sakta ha (jaise Toxicity
        #   ki polarity 3.x -> 4.x ma ulti hui). Number gire to pehle version check karo.
        # ---------------------------------------------------------
        deepeval_version = getattr(deepeval, "__version__", None)
    except Exception:
        deepeval_version = None

    embeddings = getattr(rag.retriever.store, "_embedding_function", None)

    return {
        "generator_model": getattr(gen, "GENERATOR_MODEL", None) or getattr(gen.llm, "model", None),
        "prompt_sha": _sha(getattr(gen, "PROMPT_TEMPLATE", "")),
        "citation_prompt_sha": _sha(getattr(gen, "CITATION_PROMPT_TEMPLATE", "")),
        "judge_model": judge.JUDGE_MODEL,
        "judge_base_url": judge.OLLAMA_BASE_URL,
        "retriever_fetch_k": rag.retriever.fetch_k,
        "retriever_top_k": rag.retriever.top_k,
        "reranker_model": getattr(reranker, "CROSS_ENCODER", None),
        "embedding_model": getattr(embeddings, "model", None),
        "goldens": {p.name: _sha(p.read_bytes()) for p in sorted(GOLDENS_DIR.glob("*.json"))},
        "deepeval_version": deepeval_version,
        "python": platform.python_version(),
        "git_commit": _git_commit(),
        "note": note,
    }


def _clean(value):
    """JSON-safe: NaN -> None, numpy -> python."""
    if isinstance(value, bool) or value is None or isinstance(value, str):
        return value
    try:
        f = float(value)
        return None if math.isnan(f) else f
    except Exception:
        return str(value)


# =========================================================
# RUN
# =========================================================

def resolve_suites(arg):
    names = []
    for part in [p.strip() for p in (arg or "all").split(",") if p.strip()]:
        names.extend(PRESETS.get(part, [part]))
    unknown = [n for n in names if n not in SUITES]
    if unknown:
        raise SystemExit(f"Unknown suite(s): {unknown}. Available: {list(SUITES)} + presets {list(PRESETS)}")
    return list(dict.fromkeys(names))   # unique, order same


def run_suites(names, note=""):
    rag = RagPipeline()
    run_id = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")

    snapshot = {
        "run_id": run_id,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "suites": names,
        "config": capture_config(rag, note),
        "metrics": {},
        "durations_s": {},
        "errors": {},
    }

    for name in names:
        module_path, call, flatten = SUITES[name]
        print("\n" + "#" * 70)
        print(f"# SUITE: {name}   ({module_path})")
        print("#" * 70)
        t0 = time.perf_counter()
        try:
            module = importlib.import_module(module_path)
            flat = flatten(call(module, rag))
            snapshot["metrics"].update({k: _clean(v) for k, v in flat.items()})
        except Exception as e:
            # ek suite crash ho to baqi chalti rahen; gate is suite ko FAIL maanega
            traceback.print_exc()
            snapshot["errors"][name] = f"{type(e).__name__}: {e}"
        snapshot["durations_s"][name] = round(time.perf_counter() - t0, 1)

    return snapshot


def save(snapshot):
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    run_path = RUNS_DIR / f"{snapshot['run_id']}.json"
    text = json.dumps(snapshot, indent=2)
    run_path.write_text(text, encoding="utf-8")
    LATEST_PATH.write_text(text, encoding="utf-8")
    return run_path


def print_snapshot(snapshot):
    print("\n" + "=" * 78)
    print(f"SNAPSHOT  run_id={snapshot['run_id']}  suites={','.join(snapshot['suites'])}")
    print("=" * 78)
    for key, value in snapshot["metrics"].items():
        shown = f"{value:.4f}" if isinstance(value, float) else str(value)
        print(f"  {key:<58} {shown}")
    for name, err in snapshot["errors"].items():
        print(f"  !! {name} CRASHED: {err}")
    print("-" * 78)
    print("durations (s): " + ", ".join(f"{k}={v}" for k, v in snapshot["durations_s"].items()))
    print("=" * 78)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Run eval suites and save a regression snapshot.")
    parser.add_argument("--suites", default="all", help="comma list of suites or presets (all, core, rag, safety, quick)")
    parser.add_argument("--note", default="", help="is run ma kya badla (experiment note)")
    parser.add_argument("--gate", action="store_true", help="run ke baad baseline se compare karo; regression pe exit 1")
    parser.add_argument("--list", action="store_true", help="suites aur presets dikhao")
    args = parser.parse_args(argv)

    if args.list:
        print("suites :", ", ".join(SUITES))
        for k, v in PRESETS.items():
            print(f"preset {k:<7}: {', '.join(v)}")
        return 0

    names = resolve_suites(args.suites)
    snapshot = run_suites(names, note=args.note)
    path = save(snapshot)
    print_snapshot(snapshot)
    print(f"saved -> {path}  (and {LATEST_PATH})")

    if args.gate:
        # folder ka naam digit se shuru hota ha, is liye importlib
        compare = importlib.import_module("evals.06_regression.compare")
        return compare.main(["--current", str(LATEST_PATH)])
    return 0


if __name__ == "__main__":
    sys.exit(main())
