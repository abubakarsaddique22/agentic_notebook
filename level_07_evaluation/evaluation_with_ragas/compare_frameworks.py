"""
compare_frameworks.py -- DeepEval vs RAGAS, same RAG app, side by side
=====================================================================

Dono projects ne SAME RAG app, SAME goldens aur SAME judge model (gpt-oss:20b-cloud)
pe evals chalaye. Metric ke NAAM milte julte hain lekin CALCULATE alag hote hain --
isi liye scores alag aate hain. Ye script dono ke latest numbers ek table ma rakhti ha.

Reads:
    DeepEval : <deepeval_dir>/results/latest.json   (run_evals.py ka snapshot)
    RAGAS    : experiments/<eval>_*.csv              (har eval ki latest CSV)

Writes:
    framework_comparison.md   (README / notes ma paste karne ke liye)

Run (ragas folder se):
    python compare_frameworks.py
    python compare_frameworks.py --deepeval-dir ..\\level_07_evaluation
"""

import argparse
import glob
import json
import math
import os

import pandas as pd

# (level, concept, deepeval metric slug, ragas csv prefix, ragas column, same goldens?, kaise farq ha)
PAIRS = [
    ("retriever", "Context Recall", "contextual_recall", "retriever", "context_recall", True,
     "Dono: ideal answer ke claims retrieved context ma milte hain?"),
    ("retriever", "Context Precision", "contextual_precision", "retriever", "context_precision", True,
     "Dono rank-aware: relevant chunks upar hain?"),
    ("generator", "Faithfulness", "faithfulness", "generator", "faithfulness", True,
     "Dono claims nikaal kar context se check; claim todne ka tareeqa alag"),
    ("generator", "Answer Relevancy", "answer_relevancy", "generator", "answer_relevancy", True,
     "DeepEval: statements relevant? (LLM). RAGAS: ulte sawal + embedding similarity"),
    ("pipeline", "Context Relevance", "contextual_relevancy", "pipeline", "context_relevance", False,
     "DeepEval: relevant statements / total. RAGAS: 2 judges 0/1/2 rating"),
    ("pipeline", "Faithfulness", "faithfulness", "pipeline", "faithfulness", False, "upar jaisa"),
    ("pipeline", "Answer Relevancy", "answer_relevancy", "pipeline", "answer_relevancy", False, "upar jaisa"),
    ("application", "Correctness", "correctness_geval", "application", "answer_accuracy", True,
     "DeepEval: GEval rubric. RAGAS: AnswerAccuracy (2 judges 0/2/4)"),
    ("application", "Completeness", "completeness_geval", "application", "completeness", True,
     "DeepEval: GEval rubric. RAGAS: FactualCorrectness recall (claims)"),
    ("application", "Style", "style_geval", "application", "teaching_style", True,
     "DeepEval: GEval score. RAGAS: DiscreteMetric pass/fail"),
]


def load_deepeval(deepeval_dir: str) -> dict:
    path = os.path.join(deepeval_dir, "results", "latest.json")
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f).get("metrics", {})


def ragas_value(prefix: str, col: str):
    files = sorted(glob.glob(f"experiments/{prefix}_*.csv"))
    if not files:
        return float("nan")
    df = pd.read_csv(files[-1])
    if col not in df.columns:
        return float("nan")
    return pd.to_numeric(df[col], errors="coerce").mean()


def deepeval_value(metrics: dict, level: str, slug: str):
    v = metrics.get(f"{level}.{slug}.avg_score")
    return float("nan") if v is None else float(v)


def fmt(v):
    return "  -  " if v is None or (isinstance(v, float) and math.isnan(v)) else f"{v:.3f}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--deepeval-dir", default=os.path.join("..", "level_07_evaluation"))
    args = ap.parse_args()

    de = load_deepeval(args.deepeval_dir)
    if not de:
        print(f"DeepEval snapshot nahi mila: {args.deepeval_dir}\\results\\latest.json")
        print("Pehle DeepEval project ma chalao:")
        print(f"  cd {args.deepeval_dir}")
        print("  python -m evals.06_regression.run_evals --suites retriever,generator,pipeline,application")
        print("(RAGAS column phir bhi neeche dikh raha ha.)\n")

    rows = []
    for level, concept, slug, prefix, col, same, how in PAIRS:
        d, r = deepeval_value(de, level, slug), ragas_value(prefix, col)
        diff = r - d if not (math.isnan(d) or math.isnan(r)) else float("nan")
        rows.append((level, concept, d, r, diff, "haan" if same else "NAHI", how))

    print(f"{'level':<12} {'metric':<18} {'DeepEval':>9} {'RAGAS':>9} {'diff':>8}  same goldens")
    print("-" * 72)
    for level, concept, d, r, diff, same, _ in rows:
        print(f"{level:<12} {concept:<18} {fmt(d):>9} {fmt(r):>9} {fmt(diff):>8}  {same}")

    print("\nYAAD RAKHO:")
    print("  - Har framework apne metric ko apne tareeqe se calculate karta ha -> numbers seedhe")
    print("    compare mat karo; TREND (ek hi framework ma run-to-run) compare karo.")
    print("  - Generated answers har run ma thode alag hote hain (dono projects ne apna RAG")
    print("    alag waqt pe chalaya) -- chhota farq judge/generator ka noise bhi ho sakta ha.")
    print("  - Bada farq (0.15+) = metric ki DEFINITION ka farq. Wahan dono ke reasons padho.")

    with open("framework_comparison.md", "w", encoding="utf-8") as f:
        f.write("| Level | Metric | DeepEval | RAGAS | Diff | Same goldens | How they differ |\n")
        f.write("|---|---|---|---|---|---|---|\n")
        for level, concept, d, r, diff, same, how in rows:
            f.write(f"| {level} | {concept} | {fmt(d)} | {fmt(r)} | {fmt(diff)} | {same} | {how} |\n")
    print("\nSaved: framework_comparison.md")


if __name__ == "__main__":
    main()
