"""
Code (heuristic) evaluators — tez, free, deterministic.

Evaluator ka return:
  - bool / int / float  -> key = function ka naam
  - dict {"key", "score", "comment"} -> custom naam + explanation
"""
from support_app import support_bot  # same folder se import (pehle .env load ho jati hai)

from langsmith import Client
# ---------------------------------------------------------
# Client  (class) -- LangSmith API se baat karne wala object
#   Client() .env se LANGSMITH_API_KEY / LANGSMITH_ENDPOINT khud uthata ha.
#   Constructor options: api_key, api_url, hide_inputs / hide_outputs (masking
#   function ya True), anonymizer, auto_batch_tracing (default True).
#   Is project ma use hone wale methods:
#     list_projects()                         -> projects ki list
#     list_runs(project_name, is_root, error, start_time, filter, limit) -> traces query
#     has_dataset / read_dataset / create_dataset(dataset_name, description)
#     create_examples(dataset_id, examples=[{inputs, outputs, metadata, split}])
#     list_examples(dataset_name, splits=[...], as_of="prod")  -> examples parho
#     update_dataset_tag(dataset_name, as_of=datetime, tag)   -> version ko tag
#     evaluate(target, data, evaluators, summary_evaluators, experiment_prefix,
#              metadata, max_concurrency)                     -> experiment chalao
#     push_prompt(name, object=prompt) / pull_prompt("name:tag") -> Prompt Hub
#     create_feedback(run_id, key, score, comment, correction) -> user 👍/👎
#     create_presigned_feedback_token(run_id, feedback_key)   -> bina key wala URL
#     flush()                                 -> pending traces ABHI bhej do
# ---------------------------------------------------------

DATASET_NAME = "watch-support-qa"


# ---------- Target: dataset input -> app -> output ----------
def target(inputs: dict) -> dict:
    return {"answer": support_bot(inputs["question"], prompt_version="v2")}


# ---------- Evaluators ----------
def not_empty(outputs: dict) -> bool:
    return bool(outputs["answer"].strip())


def is_concise(outputs: dict) -> dict:
    words = len(outputs["answer"].split())
    return {"key": "concise", "score": words <= 40, "comment": f"{words} words"}


def no_fake_payment_methods(outputs: dict) -> dict:
    """Bot kabhi card/bitcoin/jazzcash 'available' na kahe."""
    bad = ["credit card accepted", "bitcoin accepted", "online payment available"]
    found = [b for b in bad if b in outputs["answer"].lower()]
    return {"key": "no_fake_payment", "score": not found, "comment": ", ".join(found) or "ok"}


def mentions_key_fact(outputs: dict, example) -> dict:
    """`example` se metadata lo -> category ke hisaab se zaroori keyword check karo."""
    category = (example.metadata or {}).get("category")
    must_have = {"payment": "cod", "delivery": "din", "returns": "7", "warranty": "6"}.get(category)
    if must_have is None:
        return {"key": "key_fact", "score": None, "comment": "N/A for this category"}
    hit = must_have in outputs["answer"].lower()
    return {"key": "key_fact", "score": hit, "comment": f"expected '{must_have}'"}


if __name__ == "__main__":
    client = Client()
    results = client.evaluate(
        target,
        data=DATASET_NAME,
        evaluators=[not_empty, is_concise, no_fake_payment_methods, mentions_key_fact],
        experiment_prefix="code-evals-v2",
        description="Heuristic checks on prompt v2",
        metadata={"prompt_version": "v2"},
        max_concurrency=4,
    )

    df = results.to_pandas()
    score_cols = [c for c in df.columns if c.startswith("feedback.")]
    print(df[["inputs.question"] + score_cols].to_string())
    print("\nUI mein experiment link upar print hua hoga — wahan details dekho.")
