"""
Prompt v1 vs v2 — industry mein har prompt/model change ka yahi process hai:

  1. Same dataset, same evaluators
  2. Do experiments (purana vs naya)
  3. UI mein compare -> regressions dhoondo -> phir deploy

Summary evaluators: poore experiment par ek number (e.g. pass rate).
"""
from support_app import support_bot

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
REFUSAL_WORDS = ["sirf store", "only help", "store-related", "store se related", "madad nahi"]


# ---------- Per-example evaluators ----------
def concise(outputs: dict) -> bool:
    return len(outputs["answer"].split()) <= 40


def refuses_off_topic(outputs: dict, example) -> dict:
    if (example.metadata or {}).get("category") != "off-topic":
        return {"key": "refuses_off_topic", "score": None}
    ok = any(w in outputs["answer"].lower() for w in REFUSAL_WORDS)
    return {"key": "refuses_off_topic", "score": ok}


# ---------- Summary evaluators (poore experiment par) ----------
def concise_rate(outputs: list[dict]) -> dict:
    ok = sum(len(o["answer"].split()) <= 40 for o in outputs)
    return {"key": "concise_rate", "score": ok / len(outputs)}


def avg_words(outputs: list[dict]) -> dict:
    return {"key": "avg_words", "score": sum(len(o["answer"].split()) for o in outputs) / len(outputs)}


def make_target(version: str):
    def target(inputs: dict) -> dict:
        return {"answer": support_bot(inputs["question"], prompt_version=version)}

    return target


if __name__ == "__main__":
    client = Client()
    # Fixed version par chalana ho to: data=client.list_examples(dataset_name=DATASET_NAME, as_of="prod")
    for version in ["v1", "v2"]:
        print(f"\n===== Prompt {version} =====")
        client.evaluate(
            make_target(version),
            data=DATASET_NAME,
            evaluators=[concise, refuses_off_topic],
            summary_evaluators=[concise_rate, avg_words],
            experiment_prefix=f"prompt-{version}",
            metadata={"prompt_version": version},
            max_concurrency=4,
        )

    print("\nUI: watch-support-qa -> Experiments -> 'prompt-v1' aur 'prompt-v2' select -> Compare.")
