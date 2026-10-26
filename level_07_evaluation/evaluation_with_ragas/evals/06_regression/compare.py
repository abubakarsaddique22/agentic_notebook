"""
REGRESSION -- 2. COMPARE (quality gate)
=======================================

Naya run vs BASELINE (pichla "accha" run jo regression/baseline.json ma save ha).

Rules:
    quality metric (mean / rate, zyada behtar):
        current < baseline - tolerance        -> REGRESSION (fail)
    latency metric (p95, kam behtar):
        current > baseline * (1 + LATENCY_TOLERANCE)  -> REGRESSION (fail)
    koi eval crash hua                          -> fail
    baseline ma tha, ab nahi mila               -> warning

Tolerance kyun? LLM judge + LLM generator har run ma thoda alag score dete hain
(component level pe dekha: same data pe faithfulness 94.7% -> 86.1%). Har 1-2% ki
girawat pe build fail karoge to "flaky gate" ban jayega -- log usay ignore karne lagte hain.

Config bhi compare hota ha -- taake pata chale score KIS change se gira
(prompt hash badla? model badla?).

Exit code: 0 = sab theek (merge allowed), 1 = regression (CI merge rok de)

Run akela (latest run vs baseline):
    python -m evals.06_regression.compare
    python -m evals.06_regression.compare regression/runs/20261024-200000.json --tolerance 0.03
"""

import argparse
import glob
import json
import math
import os
import sys

LATENCY_TOLERANCE = 0.20        # p95 latency 20% tak barh sakti ha


def _load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def compare_reports(baseline_path: str, run_path: str, tolerance: float = 0.05,
                    crashed: list | None = None) -> int:
    run = _load(run_path)
    crashed = crashed if crashed is not None else run.get("crashed", [])

    print("\n" + "=" * 72)
    print("REGRESSION CHECK")
    print("=" * 72)

    if not os.path.exists(baseline_path):
        print(f"Baseline nahi mila ({baseline_path}).")
        print("Pehle ek accha run baseline banao:  python -m evals.06_regression.run_suite --set-baseline")
        return 1 if crashed else 0

    base = _load(baseline_path)
    print(f"baseline: {base['timestamp']}    current: {run['timestamp']}    tolerance: {tolerance}")

    # config diff
    changed = {k: (base["config"].get(k), v) for k, v in run["config"].items()
               if base["config"].get(k) != v}
    if changed:
        print("\nCONFIG CHANGES (score badla to inki wajah se):")
        for k, (old, new) in changed.items():
            print(f"  {k}: {old} -> {new}")

    failures, warnings = [], []
    print(f"\n{'eval':<12} {'metric':<20} {'baseline':>9} {'current':>9} {'delta':>8}  status")
    print("-" * 72)

    for name, b_eval in base["evals"].items():
        c_eval = run["evals"].get(name)
        if c_eval is None:
            warnings.append(f"{name}: is run ma nahi chala")
            continue
        for metric, b in b_eval["metrics"].items():
            c = c_eval["metrics"].get(metric)
            if c is None:
                warnings.append(f"{name}.{metric}: missing")
                continue
            bv, cv, how = b["value"], c["value"], b["how"]
            if cv is None or (isinstance(cv, float) and math.isnan(cv)):
                status = "ERROR"
                failures.append(f"{name}.{metric}: sab cases error (NaN)")
            elif how == "p95":
                limit = bv * (1 + LATENCY_TOLERANCE)
                status = "REGRESSED" if cv > limit else "ok"
                if status != "ok":
                    failures.append(f"{name}.{metric}: p95 {bv:.1f}s -> {cv:.1f}s (limit {limit:.1f}s)")
            else:
                status = "REGRESSED" if cv < bv - tolerance else ("improved" if cv > bv + tolerance else "ok")
                if status == "REGRESSED":
                    failures.append(f"{name}.{metric}: {bv:.3f} -> {cv:.3f}")
            if c.get("errors"):
                warnings.append(f"{name}.{metric}: {c['errors']} judge errors")
            delta = (cv - bv) if isinstance(cv, (int, float)) and not math.isnan(cv) else float("nan")
            print(f"{name:<12} {metric:<20} {bv:>9.3f} {cv:>9.3f} {delta:>+8.3f}  {status}")

    for name in crashed:
        failures.append(f"{name}: eval crash hua")

    if warnings:
        print("\nWARNINGS:")
        for w in warnings:
            print(f"  - {w}")

    if failures:
        print("\nQUALITY GATE: FAIL")
        for f in failures:
            print(f"  x {f}")
        return 1

    print("\nQUALITY GATE: PASS")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run", nargs="?", help="run json (default: latest regression/runs/*.json)")
    ap.add_argument("--baseline", default="regression/baseline.json")
    ap.add_argument("--tolerance", type=float, default=0.05)
    args = ap.parse_args()

    run_path = args.run
    if not run_path:
        runs = sorted(glob.glob("regression/runs/*.json"))
        if not runs:
            print("Koi run nahi mila. Pehle: python -m evals.06_regression.run_suite")
            sys.exit(1)
        run_path = runs[-1]
    sys.exit(compare_reports(args.baseline, run_path, args.tolerance))


if __name__ == "__main__":
    main()
