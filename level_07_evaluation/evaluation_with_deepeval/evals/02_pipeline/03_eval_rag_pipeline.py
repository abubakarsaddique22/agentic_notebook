"""
evals/eval_rag_pipeline.py
==========================
End-to-end evaluation of the WHOLE RAG pipeline (retrieve -> rerank -> generate)
using the RAG triad:

    ContextualRelevancy : retriever ne jo context diya, kya woh query se relevant ha?
    Faithfulness        : answer ke claims context se supported hain?
    AnswerRelevancy     : answer query ka jawab deta ha?

Setup (one time):
    pip install json-repair
    ollama signin

Run:
    python -m evals.eval_rag_pipeline
"""

print("[1] eval_rag_pipeline.py started")

# DEEPEVAL TIMEOUTS ab judge.py ma set hote hain (judge deepeval se PEHLE import hota ha)

# ---------------------------------------------------------
# IMPORT ORDER MATTERS (Windows):
# src.* (reranker -> torch / sentence-transformers / chroma) MUST be imported
# BEFORE deepeval / openai. Ulta order ma DLL conflict se process bina error
# ke chup-chaap exit ho jata ha.
# ---------------------------------------------------------
from src.rag_pipeline import RagPipeline

print("[2] pipeline imported")

from judge import get_judge                # shared Ollama judge (project root)


from dotenv import load_dotenv

from deepeval import evaluate
# ---------------------------------------------------------
# evaluate  (function)
#   DeepEval ka main "run button". Test cases + metrics leta ha, har test case
#   pe har metric chalata ha (judge LLM ko call karke), score + reason nikalta
#   ha, terminal pe table print karta ha, aur EvaluationResult wapas deta ha.
#   Arguments:
#     test_cases      -> LLMTestCase ki list (KYA check karna ha)
#     metrics         -> metric objects ki list (KIS cheez pe check karna ha)
#     async_config    -> AsyncConfig (parallel kitna chalana ha) -- optional
#     hyperparameters -> dict, sirf record/logging ke liye (model, top_k, waghera).
#                        Score pe asar NAHI, bas runs compare karne ke kaam aata ha.
#   Return: EvaluationResult -> .test_results (list). Har item ma:
#     .name, .input, .actual_output, .success, aur .metrics_data (list) jis ma
#     har metric ka .name, .score, .success, .reason hota ha.
# ---------------------------------------------------------
from deepeval.evaluate.configs import AsyncConfig
# ---------------------------------------------------------
# AsyncConfig  (settings class)
#   evaluate() ko batata ha ke test cases ko parallel (async) kaise chalaye.
#     run_async      -> True (default) = async, False = ek ek karke (sequential)
#     max_concurrent -> ek waqt ma kitne test cases saath chalein (default 20,
#                       Ollama ke liye zyada ha -- is liye 1 ya 2 rakhte hain)
#     throttle_value -> har test case se pehle kitne second ruko (default 0),
#                       rate limit (429) se bachne ke liye
#   Note: ye TEST CASE level ki limit ha. Ek test case ke andar metric kai judge
#   calls bhej sakta ha -- un ko judge.py ka semaphore control karta ha.
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
#   Yahan: input + actual_output (pipeline ka LIVE jawab) + retrieval_context
#   (pipeline ne jo chunks khud retrieve kiye). expected_output nahi chahiye.
# ---------------------------------------------------------
from deepeval.metrics import (
    FaithfulnessMetric,
    AnswerRelevancyMetric,
    ContextualRelevancyMetric,
)
# ---------------------------------------------------------
# ContextualRelevancyMetric  (retriever metric -- context kitna kaam ka)
#   Sawal: "Retriever ne jo context diya, us ma kitna hissa sawal se RELEVANT ha?"
#   Kaise: judge retrieval_context ko statements ma todta ha aur har statement
#          ko input (sawal) ke against relevant / irrelevant mark karta ha.
#   Score = (relevant statements) / (total statements)  -> 0 se 1
#   Chahiye: input, retrieval_context   (expected_output nahi chahiye)
#   Low score = context ma kachra zyada (top_k bara, chunks bare, reranker kamzor)
#
# FaithfulnessMetric  (generator metric -- hallucination check)
#   Sawal: "Kya jawab ki har baat diye gaye context se SABIT hoti ha?"
#   Kaise: judge actual_output se claims nikalta ha, retrieval_context se facts
#          nikalta ha, phir har claim check karta ha ke context use contradict
#          to nahi karta.
#   Score = (wo claims jo context ke khilaf nahi) / (total claims)  -> 0 se 1
#   Chahiye: input, actual_output, retrieval_context
#   Low score = model apni taraf se baatein bana raha ha (hallucination)
#
# AnswerRelevancyMetric  (generator metric -- on-topic check)
#   Sawal: "Kya jawab ASAL sawal ka hi jawab ha, ya idhar udhar ki baatein?"
#   Kaise: judge actual_output ko statements ma todta ha, har statement ko input
#          ke against relevant / irrelevant mark karta ha.
#   Score = (relevant statements) / (total statements)  -> 0 se 1
#   Chahiye: input, actual_output   (context ya expected_output nahi chahiye)
#   Low score = jawab off-topic ha ya sawal ko miss kar gaya
#
# Common attributes (constructor arguments):
#   threshold      -> pass/fail ki line
#   model          -> judge LLM (OllamaJudge). Na do to DeepEval default OpenAI model lega
#   include_reason -> True = score ke saath "kyun" bhi likhe
#   strict_mode    -> True = score sirf 0 ya 1
#   async_mode     -> (optional, default True) andar ki judge calls async
#   verbose_mode   -> (optional) andar ke steps print kare
# Run ke baad metric pe milte hain: .score, .reason, .success
#
# RAG TRIAD: ContextualRelevancy (retriever) + Faithfulness + AnswerRelevancy
# (generator). Teeno reference-free hain -- golden answer ki zaroorat nahi.
# ---------------------------------------------------------

from harness import load_goldens, summarize_by_metric, print_summary

print("[3] deepeval imported")

load_dotenv()

GOLDEN_PATH = "goldens/faithfulness_dataset.json"   # sirf queries reuse ho rahi hain
THRESHOLD = 0.7
MAX_CONCURRENT = 1                                  # 1 = sab se stable, 2 = tez lekin risky


# =========================================================
# EVAL
# =========================================================

def run(rag):
    # 1. LOAD queries (sirf queries chahiye, context ab pipeline se aata ha)
    goldens = load_goldens(GOLDEN_PATH)
    print(f"Loaded {len(goldens)} queries from {GOLDEN_PATH}")

    # 2. RUN THE PIPELINE per query, LIVE output se test case banao
    test_cases = []
    for g in goldens:
        result = rag.invoke(g["query"])          # retrieve -> rerank -> generate

        test_cases.append(
            LLMTestCase(
                input=g["query"],    # sawal / user message
                actual_output=result["answer"],       # generator ka answer
                retrieval_context=result["context"],  # retriever ne jo diya
            )
        )

    # 3. JUDGE: sirf ek dafa, loop ke BAHAR
    judge = get_judge()

    # 4. THE THREE TRIAD METRICS
    metrics = [
        ContextualRelevancyMetric(threshold=THRESHOLD, model=judge, include_reason=True),
        FaithfulnessMetric(threshold=THRESHOLD, model=judge, include_reason=True),
        AnswerRelevancyMetric(threshold=THRESHOLD, model=judge, include_reason=True),
    ]

    # 5. EVALUATE
    result = evaluate(
        test_cases=test_cases,    # kya check karna ha (LLMTestCase list)
        metrics=metrics,    # kin metrics pe check karna ha
        async_config=AsyncConfig(max_concurrent=MAX_CONCURRENT),    # ek waqt ma MAX_CONCURRENT test cases
    )
    return summarize_by_metric(result)


def run_local():
    """Standalone convenience: pipeline banao, phir run karo."""
    return run(RagPipeline())


if __name__ == "__main__":
    print_summary("rag_pipeline", run_local())