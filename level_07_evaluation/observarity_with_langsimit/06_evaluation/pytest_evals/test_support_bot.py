"""
pytest + LangSmith = CI/CD mein evals.

@pytest.mark.langsmith lagane se:
  - har test case LangSmith mein ek example ki tarah log hota hai (dataset khud ban jata hai)
  - har run ek experiment banta hai -> history mein dekh sakte ho kab regression aaya
  - t.log_feedback se custom scores bhi jate hain

Chalao (root folder se):
    pytest 06_evaluation\\pytest_evals -v

GitHub Actions mein bhi yahi command chalti hai (secrets mein API keys).
"""
import pytest
from langsmith import testing as t
# ---------------------------------------------------------
# langsmith.testing as t  -- pytest ke andar LangSmith logging
#   @pytest.mark.langsmith laga ho to har test ek dataset example + experiment
#   run ban jata ha. Andar ye functions:
#     t.log_inputs({...})            -> test ka input
#     t.log_reference_outputs({...}) -> expected / sahi jawab
#     t.log_outputs({...})           -> app ka asal output
#     t.log_feedback(key, score)     -> custom score (word_count, waghera)
#   assert fail = test fail = LangSmith ma bhi fail dikhega.
# ---------------------------------------------------------
from support_app import support_bot

CASES = [
    ("Kya card se payment ho sakti hai?", "cod"),
    ("Exchange kitne din mein ho sakta hai?", "7"),
    ("Warranty kitni hai?", "6"),
]


@pytest.mark.langsmith
@pytest.mark.parametrize("question,must_contain", CASES)
def test_answer_contains_key_fact(question: str, must_contain: str):
    t.log_inputs({"question": question})
    t.log_reference_outputs({"must_contain": must_contain})

    answer = support_bot(question, prompt_version="v2")
    t.log_outputs({"answer": answer})

    word_count = len(answer.split())
    t.log_feedback(key="word_count", score=word_count)

    assert must_contain in answer.lower(), f"'{must_contain}' missing in: {answer}"
    assert word_count <= 40


@pytest.mark.langsmith
def test_refuses_off_topic():
    question = "Python mein list kaise sort karte hain?"
    t.log_inputs({"question": question})
    answer = support_bot(question, prompt_version="v2")
    t.log_outputs({"answer": answer})

    # Off-topic sawal par code nahi likhna chahiye
    assert "sorted(" not in answer and ".sort(" not in answer
