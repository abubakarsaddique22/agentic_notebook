"""
Level 9: saare modules ke scripts ek saath OFFLINE chalao (koi API key nahi chahiye).
Har script ka PASS/FAIL aur waqt batata hai. Setup check karne ke liye best.

    python run_all_offline.py            # summary only
    python run_all_offline.py --show     # har script ka poora output bhi
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent

SCRIPTS = [
    ("M9.1 cost & latency estimator", ["01_design_framework/cost_latency_estimator.py"]),
    ("M9.2 knowledge pipeline", ["02_context_knowledge/knowledge_pipeline.py", "--offline"]),
    ("M9.3 gateway (LiteLLM mock)", ["03_model_routing_gateway/gateway.py", "--mock"]),
    ("M9.4 latency lab (simulation)", ["04_latency_optimization/latency_lab.py", "--mock"]),
    ("M9.5 caching lab", ["05_caching/caching_lab.py", "--offline"]),
    ("M9.6 reliability (chaos)", ["06_reliability_guardrails/reliability.py"]),
    ("M9.7 orchestration (FastAPI)", ["07_pipeline_orchestration/try_app.py"]),
    ("M9.8 monitoring lab", ["08_monitoring_feedback/monitoring_lab.py"]),
]


def main() -> None:
    show = "--show" in sys.argv
    env = {**os.environ, "PYTHONIOENCODING": "utf-8", "LLM_MODE": "mock"}
    env.pop("GROQ_API_KEY", None)          # offline guarantee
    results = []
    for name, args in SCRIPTS:
        t = time.perf_counter()
        p = subprocess.run([sys.executable, *args], cwd=ROOT, env=env, capture_output=True,
                           text=True, encoding="utf-8", errors="replace", timeout=600)
        dt = time.perf_counter() - t
        ok = p.returncode == 0
        results.append((name, ok, dt))
        print(f"{'PASS' if ok else 'FAIL'}  {dt:5.1f}s  {name}")
        if show or not ok:
            print(p.stdout[-4000:])
            if p.stderr.strip():
                print(p.stderr[-3000:])
    passed = sum(ok for _, ok, _ in results)
    print(f"\n{passed}/{len(results)} passed")
    sys.exit(0 if passed == len(results) else 1)


if __name__ == "__main__":
    main()
