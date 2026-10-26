"""
LLM-as-judge: doosra LLM tumhare output ko grade karta hai.

1. Apna custom judge — business rules (grounded + polite) — ek call se 2 scores (list[Evaluation])
2. autoevals ka ready-made Factuality judge

Langfuse UI mein bhi "LLM-as-a-Judge" evaluators hain (bina code, folder 08 guide) —
code wale judges CI aur offline experiments ke liye, UI wale production traces ke liye.

Tip: kabhi kabhi judge ke scores ko human labels se check karo — judge bhi galat ho sakta hai.
"""
import json
import os

from support_app import support_bot

from autoevals.llm import Factuality
from langfuse import Evaluation, get_client
from langfuse.openai import OpenAI

DATASET_NAME = "watch-support-qa"
JUDGE_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
langfuse = get_client()
judge_client = OpenAI()  # judge ki calls bhi trace hongi (experiment trace ke andar)


def task(*, item, **kwargs) -> str:
    return support_bot(item.input["question"], prompt_version="v2")


# ---------- 1) Custom judge ----------
JUDGE_PROMPT = """You are grading a customer-support reply for a watch store.

Customer question: {question}
Reference answer: {reference}
Bot reply: {answer}

Check:
- grounded: Does the reply avoid inventing any fact not in the reference? (true/false)
- polite: Is the tone polite and professional? (true/false)

Return JSON: {{"grounded": bool, "polite": bool, "reasoning": "one sentence"}}"""


def custom_judge(*, input, output, expected_output, **kwargs) -> list[Evaluation]:
    resp = judge_client.chat.completions.create(
        model=JUDGE_MODEL,
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "user",
                "content": JUDGE_PROMPT.format(
                    question=input["question"], reference=expected_output["answer"], answer=output
                ),
            }
        ],
        name="custom-judge",
    )
    verdict = json.loads(resp.choices[0].message.content)
    return [
        Evaluation(name="grounded", value=1 if verdict["grounded"] else 0, comment=verdict["reasoning"]),
        Evaluation(name="polite", value=1 if verdict["polite"] else 0),
    ]


# ---------- 2) autoevals Factuality ----------
factuality = Factuality(model=JUDGE_MODEL)


def factuality_eval(*, input, output, expected_output, **kwargs) -> Evaluation:
    # autoevals ko plain strings chahiye -> dict se nikal kar do
    r = factuality(input=input["question"], output=output, expected=expected_output["answer"])
    return Evaluation(name="factuality", value=r.score, comment=(r.metadata or {}).get("rationale"))

# NOTE: Agar tumhara input/output/expected pehle se plain strings hain, to shortcut:
#   from langfuse.experiment import create_evaluator_from_autoevals
#   evaluators=[create_evaluator_from_autoevals(Factuality())]


if __name__ == "__main__":
    dataset = langfuse.get_dataset(DATASET_NAME)
    result = dataset.run_experiment(
        name="llm-judge",
        run_name="prompt-v2-llm-judge",
        description="Custom judge + autoevals Factuality on prompt v2",
        task=task,
        evaluators=[custom_judge, factuality_eval],
        max_concurrency=4,
        metadata={"prompt_version": "v2", "judge_model": JUDGE_MODEL},
    )
    print(result.format())
    langfuse.flush()
    print("UI: run kholo -> har score par hover/click -> judge ka comment (reasoning).")
