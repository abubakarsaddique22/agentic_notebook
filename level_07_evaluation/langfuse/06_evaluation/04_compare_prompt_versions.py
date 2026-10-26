"""
Prompt v1 vs v2 — har prompt/model change ka industry process:

  1. Same dataset, same evaluators
  2. Do runs (purana vs naya) — alag run_name
  3. UI mein compare -> regressions dhoondo -> phir production mein (folder 07: label move)
"""
from support_app import support_bot

from langfuse import Evaluation, get_client

DATASET_NAME = "watch-support-qa"
REFUSAL_WORDS = ["sirf store", "only help", "store-related", "store se related", "madad nahi"]
langfuse = get_client()


def concise(*, output, **kwargs) -> Evaluation:
    return Evaluation(name="concise", value=1 if len(output.split()) <= 40 else 0)


def refuses_off_topic(*, output, metadata, **kwargs):
    if (metadata or {}).get("category") != "off-topic":
        return []
    ok = any(w in output.lower() for w in REFUSAL_WORDS)
    return Evaluation(name="refuses_off_topic", value=1 if ok else 0)


def avg_words(*, item_results, **kwargs) -> Evaluation:
    counts = [len(str(r.output).split()) for r in item_results if r.output is not None]
    return Evaluation(name="avg_words", value=sum(counts) / len(counts) if counts else 0)


def make_task(version: str):
    def task(*, item, **kwargs) -> str:
        return support_bot(item.input["question"], prompt_version=version)

    return task


if __name__ == "__main__":
    dataset = langfuse.get_dataset(DATASET_NAME)
    for version in ["v1", "v2"]:
        print(f"\n===== Prompt {version} =====")
        result = dataset.run_experiment(
            name="prompt-comparison",
            run_name=f"prompt-{version}",
            task=make_task(version),
            evaluators=[concise, refuses_off_topic],
            run_evaluators=[avg_words],
            max_concurrency=4,
            metadata={"prompt_version": version},
        )
        print(result.format())

    langfuse.flush()
    print("\nUI: Datasets -> watch-support-qa -> Runs -> 'prompt-v1' + 'prompt-v2' select -> Compare.")
