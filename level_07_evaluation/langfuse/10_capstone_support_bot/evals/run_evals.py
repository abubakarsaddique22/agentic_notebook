"""
Capstone evals — har change (prompt / model / retriever) se pehle chalao.

Chalao (10_capstone_support_bot folder se, APP_ENV=development mein):
    python -m evals.run_evals --name baseline
    python -m evals.run_evals --name new-prompt --split edge-cases

Evaluators:
  - retrieval_hit    : sahi FAQ document retrieve hua?        (retriever quality)
  - concise          : 60 words se kam?                       (format)
  - no_invented_pay  : fake payment method to nahi bataya?    (business rule)
  - factuality       : LLM-as-judge (autoevals) vs reference  (quality)
Run evaluator:
  - retrieval_accuracy
"""
import argparse

from app.settings import APP_VERSION, EVAL_DATASET, MODEL, SAMPLE_RATE, langfuse

from app.bot import respond
from autoevals.llm import Factuality
from langfuse import Evaluation


# ---------- Task ----------
def task(*, item, **kwargs) -> dict:
    return respond(item.input["question"])  # {"answer", "sources"}


# ---------- Item evaluators ----------
def retrieval_hit(*, output, expected_output, **kwargs):
    expected = expected_output.get("expected_source")
    if expected is None:  # edge cases ka koi expected doc nahi -> score skip
        return []
    return Evaluation(name="retrieval_hit", value=1 if expected in output["sources"] else 0)


def concise(*, output, **kwargs) -> Evaluation:
    words = len(output["answer"].split())
    return Evaluation(name="concise", value=1 if words <= 60 else 0, comment=f"{words} words")


def no_invented_pay(*, output, **kwargs) -> Evaluation:
    text = output["answer"].lower()
    claims = ["card accepted", "jazzcash available", "easypaisa available", "bank transfer kar"]
    bad = [c for c in claims if c in text]
    return Evaluation(name="no_invented_pay", value=0 if bad else 1, comment=", ".join(bad) or "ok")


_factuality = Factuality(model=MODEL)


def factuality(*, input, output, expected_output, **kwargs) -> Evaluation:
    r = _factuality(input=input["question"], output=output["answer"], expected=expected_output["answer"])
    return Evaluation(name="factuality", value=r.score, comment=(r.metadata or {}).get("rationale"))


# ---------- Run evaluator ----------
def retrieval_accuracy(*, item_results, **kwargs) -> Evaluation:
    hits = [e.value for r in item_results for e in r.evaluations if e.name == "retrieval_hit"]
    if not hits:
        return Evaluation(name="retrieval_accuracy", value=0, comment="no data")
    return Evaluation(name="retrieval_accuracy", value=sum(hits) / len(hits))


def load_items(split: str | None):
    dataset = langfuse.get_dataset(EVAL_DATASET)
    items = [it for it in dataset.items if str(it.status).upper().endswith("ACTIVE")]
    if split:
        items = [it for it in items if (it.metadata or {}).get("split") == split]
    return items


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", default="run", help="change ka naam, e.g. baseline / shorter-prompt")
    parser.add_argument("--split", default=None, help="sirf ek split, e.g. edge-cases")
    args = parser.parse_args()

    if SAMPLE_RATE < 1.0:
        raise SystemExit("Evals production sampling ke saath mat chalao. .env mein APP_ENV=development karo.")

    items = load_items(args.split)
    print(f"{len(items)} items (split={args.split or 'all'})")

    result = langfuse.run_experiment(
        name="capstone-evals",
        run_name=f"v{APP_VERSION}-{args.name}{'-' + args.split if args.split else ''}",
        description=f"change: {args.name}",
        data=items,
        task=task,
        evaluators=[retrieval_hit, concise, no_invented_pay, factuality],
        run_evaluators=[retrieval_accuracy],
        max_concurrency=4,
        metadata={"app_version": APP_VERSION, "model": MODEL, "change": args.name},
    )
    print(result.format())
    langfuse.flush()
