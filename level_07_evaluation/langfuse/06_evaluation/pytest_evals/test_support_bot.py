"""
CI/CD gate: experiment chalao, aur agar koi zaroori case fail ho to test fail -> deploy ruk jaye.
Har CI run Langfuse mein ek experiment ki tarah save hota hai (history + link).

Chalao (root folder se):
    pytest 06_evaluation\\pytest_evals -v -s
(-s se experiment ka link CI logs mein dikhta hai)

GitHub Actions mein yahi command, keys secrets mein.
"""
from langfuse import Evaluation, get_client
from support_app import support_bot

CASES = [
    {"id": "card-payment", "input": "Kya card se payment ho sakti hai?", "must_contain": "cod"},
    {"id": "exchange-days", "input": "Exchange kitne din mein ho sakta hai?", "must_contain": "7"},
    {"id": "warranty", "input": "Warranty kitni hai?", "must_contain": "6"},
]


def task(*, item, **kwargs) -> str:
    return support_bot(item["input"], prompt_version="v2")


def key_fact(*, output, expected_output, **kwargs) -> Evaluation:
    return Evaluation(name="key_fact", value=1 if expected_output in output.lower() else 0)


def concise(*, output, **kwargs) -> Evaluation:
    return Evaluation(name="concise", value=1 if len(output.split()) <= 40 else 0)


def test_support_bot_quality_gate():
    langfuse = get_client()
    try:
        result = langfuse.run_experiment(
            name="ci-quality-gate",
            data=[
                {"input": c["input"], "expected_output": c["must_contain"], "metadata": {"case_id": c["id"]}}
                for c in CASES
            ],
            task=task,
            evaluators=[key_fact, concise],
            max_concurrency=3,
        )
        print(result.format(include_item_results=True))

        # Har case ka result aana chahiye
        returned = sorted(r.item["metadata"]["case_id"] for r in result.item_results)
        assert returned == sorted(c["id"] for c in CASES), "Kuch cases ka result missing hai"

        # Har case par har check pass
        for r in result.item_results:
            failed = [e.name for e in r.evaluations if e.value != 1]
            assert not failed, f"{r.item['metadata']['case_id']} fail: {failed} | output: {r.output}"
    finally:
        langfuse.flush()
