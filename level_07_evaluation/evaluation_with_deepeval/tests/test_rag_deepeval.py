"""
tests/test_rag_deepeval.py
==========================
REGRESSION SUITE -- step 3: pytest-style "unit tests" for the LLM app.

run_evals.py = poori suite, numbers + baseline compare (slow, nightly / before release)
ye file      = chote, tez, pass/fail tests (har commit / PR pe)

Har test ek golden case ha. assert_test() metric chalata ha aur threshold se
neeche ho to test FAIL -- bilkul normal pytest ki tarah.

Run (project root se):
    deepeval test run tests/test_rag_deepeval.py        # DeepEval ka runner (report ke saath)
    pytest tests -q                                     # ya plain pytest

Ek test:
    pytest tests -q -k injection
"""

# IMPORT ORDER (Windows): src.* -> judge -> deepeval
from src.rag_pipeline import RagPipeline
from src.generator import generate

from judge import get_judge
from programmatic import CanaryLeakMetric, CitationPresenceMetric, CitationValidityMetric
from harness import load_goldens

from pathlib import Path

import pytest
from deepeval import assert_test
# ---------------------------------------------------------
# assert_test  (function -- pytest ke liye)
#   assert_test(test_case, metrics) ek test case pe saare metrics chalata ha.
#   Koi bhi metric threshold se neeche ho -> AssertionError -> pytest test FAIL.
#   Yani evaluate() ka "unit test" version: evaluate() report deta ha,
#   assert_test() pass/fail deta ha (CI / har PR ke liye).
#   Run: `deepeval test run tests/...` (DeepEval report ke saath) ya plain `pytest`.
#   Arguments:
#     test_case -> ek LLMTestCase
#     metrics   -> metrics ki list
# ---------------------------------------------------------
from deepeval.test_case import LLMTestCase
# ---------------------------------------------------------
# LLMTestCase  (data container class)
#   Ek "test case" = ek sawal aur us se judi saari cheezen. Metrics isi object
#   se fields parhte hain. Khud koi kaam nahi karta, sirf data rakhta ha.
#   Attributes (jo is project ma use hote hain):
#     input               -> user ka sawal / message
#     actual_output       -> aap ke system ne jo jawab diya (yahi test hota ha)
#     expected_output     -> sahi / ideal jawab ya expected behaviour (golden se)
#     retrieval_context   -> wo chunks jo generator ko diye gaye (list of strings)
#     name                -> test case ka naam/id (report ma isi se pehchante hain)
#     additional_metadata -> apna extra data (dict). Metric score pe asar nahi,
#                            lekin hamare programmatic metrics isay parhte hain.
#                            (naye 4.x ma iska naya naam `metadata` ha)
#   Har pytest function ek LLMTestCase banata ha aur assert_test ko deta ha.
# ---------------------------------------------------------
from deepeval.metrics import FaithfulnessMetric
# ---------------------------------------------------------
# FaithfulnessMetric  (generator metric -- hallucination check)
#   Sawal: "Kya jawab ki har baat diye gaye context se SABIT hoti ha?"
#   Kaise: judge actual_output se claims nikalta ha, retrieval_context se facts
#          nikalta ha, phir har claim check karta ha ke context use contradict
#          to nahi karta.
#   Score = (wo claims jo context ke khilaf nahi) / (total claims)  -> 0 se 1
#   Chahiye: input, actual_output, retrieval_context
#   Low score = model apni taraf se baatein bana raha ha (hallucination)
#
# Common attributes (constructor arguments):
#   threshold      -> pass/fail ki line
#   model          -> judge LLM (OllamaJudge). Na do to DeepEval default OpenAI model lega
#   include_reason -> True = score ke saath "kyun" bhi likhe
#   strict_mode    -> True = score sirf 0 ya 1
#   async_mode     -> (optional, default True) andar ki judge calls async
#   verbose_mode   -> (optional) andar ke steps print kare
# Run ke baad metric pe milte hain: .score, .reason, .success
# ---------------------------------------------------------

ROOT = Path(__file__).resolve().parents[1]
N_CASES = 3          # har group se kitne cases (chota rakho -- ye har PR pe chalega)

INJECTION = [g for g in load_goldens(ROOT / "goldens/injection_goldens.json") if g["poison_chunk"]][:N_CASES]
FAITHFULNESS = load_goldens(ROOT / "goldens/faithfulness_dataset.json")[:N_CASES]
CITATION = load_goldens(ROOT / "goldens/correctness_goldens.json")[:N_CASES]


@pytest.fixture(scope="session")
def rag():
    # ek hi dafa load (chroma + reranker model)
    return RagPipeline()


# ---------------------------------------------------------
# 1. SAFETY: poisoned context ka canary answer ma nahi aana chahiye (programmatic, no judge)
# ---------------------------------------------------------
@pytest.mark.parametrize("g", INJECTION, ids=[g["id"] for g in INJECTION])
def test_injection_canary_not_leaked(rag, g):
    docs = rag.retriever.invoke(g["query"])
    context = [d.page_content for d in docs]
    context.insert(0, g["poison_chunk"])

    answer = generate(g["query"], context)

    test_case = LLMTestCase(
        input=g["query"],    # sawal / user message
        actual_output=answer,    # bot ka jawab -- yahi test ho raha ha
        retrieval_context=context,    # wo chunks jo generator ko diye gaye
        additional_metadata={"canary": g["canary"]},    # apna extra data -- programmatic metrics yahan se parhte hain
    )
    assert_test(test_case, [CanaryLeakMetric()])


# ---------------------------------------------------------
# 2. GENERATOR: golden context pe answer faithful ho (LLM judge)
# ---------------------------------------------------------
@pytest.mark.parametrize("g", FAITHFULNESS, ids=[g["id"] for g in FAITHFULNESS])
def test_generator_faithfulness(g):
    answer = generate(g["query"], g["ideal_context"])

    test_case = LLMTestCase(
        input=g["query"],    # sawal / user message
        actual_output=answer,    # bot ka jawab -- yahi test ho raha ha
        retrieval_context=g["ideal_context"],    # wo chunks jo generator ko diye gaye
    )
    assert_test(test_case, [FaithfulnessMetric(threshold=0.7, model=get_judge())])


# ---------------------------------------------------------
# 3. CITATIONS: citation ho, aur sirf retrieved sessions ki ho (programmatic, no judge)
# ---------------------------------------------------------
@pytest.mark.parametrize("g", CITATION, ids=[g["id"] for g in CITATION])
def test_citations_present_and_valid(rag, g):
    result = rag.invoke_with_citations(g["question"])

    test_case = LLMTestCase(
        input=g["question"],    # sawal / user message
        actual_output=result["answer"],    # bot ka jawab -- yahi test ho raha ha
        retrieval_context=result["context"],    # wo chunks jo generator ko diye gaye
        additional_metadata={"retrieved_sessions": result["sessions"]},    # apna extra data -- programmatic metrics yahan se parhte hain
    )
    assert_test(test_case, [CitationPresenceMetric(), CitationValidityMetric()])
