"""
Local data par experiment — dataset banaye bina jaldi test.
(Prototype stage mein useful. Serious kaam ke liye dataset — file 02.)

local data: item ek dict hai -> item["input"], item["expected_output"]
"""
from support_app import support_bot  # same folder (yeh .env bhi load karta hai)

from langfuse import Evaluation, get_client

langfuse = get_client()

LOCAL_DATA = [
    {"input": "Warranty kitni hai?", "expected_output": "6"},
    {"input": "Card se payment ho sakti hai?", "expected_output": "cod"},
    {"input": "Exchange kitne din mein?", "expected_output": "7"},
]


def task(*, item, **kwargs) -> str:
    return support_bot(item["input"], prompt_version="v2")


def contains_key_fact(*, output, expected_output, **kwargs) -> Evaluation:
    hit = expected_output.lower() in output.lower()
    return Evaluation(name="contains_key_fact", value=1 if hit else 0, comment=f"expected '{expected_output}'")


def word_count(*, output, **kwargs) -> Evaluation:
    return Evaluation(name="word_count", value=len(output.split()))


if __name__ == "__main__":
    result = langfuse.run_experiment(
        name="quick-local-check",
        description="Prompt v2 ka jaldi check, bina dataset ke",
        data=LOCAL_DATA,
        task=task,
        evaluators=[contains_key_fact, word_count],
    )
    print(result.format(include_item_results=True))  # har item ka input/output/score bhi
    langfuse.flush()
