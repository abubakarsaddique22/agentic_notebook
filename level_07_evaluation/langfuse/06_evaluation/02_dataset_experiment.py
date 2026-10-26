"""
Langfuse dataset par experiment (industry ka standard).

  - dataset item: item.input, item.expected_output, item.metadata
  - code (heuristic) evaluators — tez, free, deterministic
  - run evaluator — poore run ka ek number
  - split filter — sirf "edge-cases" par chalana ho to
"""
import sys

from support_app import support_bot

from langfuse import Evaluation, get_client

DATASET_NAME = "watch-support-qa"
langfuse = get_client()


# ---------- Task ----------
def task(*, item, **kwargs) -> str:
    return support_bot(item.input["question"], prompt_version="v2")


# ---------- Item evaluators ----------
def not_empty(*, output, **kwargs) -> Evaluation:
    return Evaluation(name="not_empty", value=1 if output.strip() else 0)


def concise(*, output, **kwargs) -> Evaluation:
    words = len(output.split())
    return Evaluation(name="concise", value=1 if words <= 40 else 0, comment=f"{words} words")


def no_fake_payment(*, output, **kwargs) -> Evaluation:
    bad = ["credit card accepted", "bitcoin accepted", "online payment available"]
    found = [b for b in bad if b in output.lower()]
    return Evaluation(name="no_fake_payment", value=0 if found else 1, comment=", ".join(found) or "ok")


def key_fact(*, output, metadata, **kwargs):
    """metadata se category -> zaroori keyword. Jis category par lagu nahi, wahan [] (score skip)."""
    category = (metadata or {}).get("category")
    must_have = {"payment": "cod", "delivery": "din", "returns": "7", "warranty": "6"}.get(category)
    if must_have is None:
        return []
    hit = must_have in output.lower()
    return Evaluation(name="key_fact", value=1 if hit else 0, comment=f"expected '{must_have}'")


# ---------- Run evaluator (summary) ----------
def concise_rate(*, item_results, **kwargs) -> Evaluation:
    values = [e.value for r in item_results for e in r.evaluations if e.name == "concise"]
    if not values:
        return Evaluation(name="concise_rate", value=0, comment="no data")
    return Evaluation(name="concise_rate", value=sum(values) / len(values))


def load_items(split: str | None):
    dataset = langfuse.get_dataset(DATASET_NAME)
    items = [it for it in dataset.items if str(it.status).upper().endswith("ACTIVE")]
    if split:
        items = [it for it in items if (it.metadata or {}).get("split") == split]
    return items


if __name__ == "__main__":
    split = sys.argv[1] if len(sys.argv) > 1 else None  # e.g. python ... 02_dataset_experiment.py edge-cases
    items = load_items(split)
    print(f"{len(items)} items par experiment (split={split or 'all'})")

    result = langfuse.run_experiment(
        name="code-evals",
        run_name=f"prompt-v2-code-evals{'-' + split if split else ''}",
        description="Heuristic checks on prompt v2",
        data=items,  # DatasetItems -> run dataset se link hota hai (UI: Datasets -> Runs)
        task=task,
        evaluators=[not_empty, concise, no_fake_payment, key_fact],
        run_evaluators=[concise_rate],
        max_concurrency=4,
        metadata={"prompt_version": "v2"},
    )
    print(result.format())
    langfuse.flush()
