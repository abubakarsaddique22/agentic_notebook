# eval_retriever.py
from dotenv import load_dotenv

# IMPORT ORDER (Windows): src.* -> judge -> deepeval
from src.reranker import RerankingRetriever

from judge import get_judge, JUDGE_MODEL      # shared Ollama judge (project root)

from deepeval import evaluate
# ---------------------------------------------------------
# evaluate  (function)
#   DeepEval ka main "run button". Aap isay test cases ki list aur metrics
#   ki list dete ho, ye har test case pe har metric chalata ha (judge LLM
#   ko call karta ha), score + reason nikalta ha, terminal pe table print
#   karta ha, aur ek EvaluationResult object wapas deta ha.
#   Main arguments (neeche use hue hain):
#     test_cases      -> LLMTestCase objects ki list (kya check karna ha)
#     metrics         -> metric objects ki list (kis cheez pe check karna ha)
#     async_config    -> AsyncConfig object (parallel kitna chalana ha)
#     hyperparameters -> dict, sirf record/logging ke liye (kaunsa model,
#                        chunk_size, top_k waghera). Score pe asar NAHI hota,
#                        bas baad ma runs compare karne ke kaam aata ha.
#   Return: EvaluationResult -> .test_results list, har item ma
#           .metrics_data (name, score, success, reason) hota ha.
#           harness.summarize_by_metric() isi ko parhta ha.
# ---------------------------------------------------------

from deepeval.evaluate.configs import AsyncConfig
# ---------------------------------------------------------
# AsyncConfig  (class / settings object)
#   evaluate() ko batata ha ke test cases ko parallel (async) kaise chalaye.
#   Attributes:
#     run_async      -> True (default) = async mode on, False = ek ek karke
#     max_concurrent -> ek waqt ma kitne test cases saath chalein
#                       (default 20 -- Ollama ke liye bohat zyada, is liye 2 rakha)
#     throttle_value -> har test case shuru karne se pehle kitne second ruke
#                       (rate limit se bachne ke liye), default 0
#   Note: ye TEST CASE level ki limit ha. Ek test case ke andar metric khud
#   kai judge calls bhej sakta ha -- us ko judge.py ka semaphore control karta ha.
# ---------------------------------------------------------

from deepeval.test_case import LLMTestCase
# ---------------------------------------------------------
# LLMTestCase  (class / data container)
#   Ek "test case" = ek sawal aur us se judi saari cheezen. Metrics isi
#   object se fields parhte hain. Khud koi kaam nahi karta, sirf data rakhta ha.
#   Attributes:
#     input             -> user ka sawal (query)
#     actual_output     -> aap ke system ne jo jawab diya
#     expected_output   -> sahi / ideal jawab (golden set se)
#     retrieval_context -> retriever ne jo chunks laaye (list of strings)
#     context           -> (optional) ideal/ground-truth context, yahan use nahi
#   Har metric ko alag fields chahiye. Retriever metrics ko actual_output ki
#   zaroorat nahi, is liye yahan placeholder string diya ha.
# ---------------------------------------------------------

from deepeval.metrics import (
    ContextualRecallMetric,
    ContextualPrecisionMetric,
)
# ---------------------------------------------------------
# ContextualRecallMetric  (retriever metric)
#   Sawal: "Kya retriever ne WOH SAB laya jo sahi jawab ke liye zaroori tha?"
#   Kaise: judge expected_output ko chhote statements ma todta ha, phir har
#          statement check karta ha ke retrieval_context ma us ka saboot ha ya nahi.
#   Score = (jin statements ka saboot mila) / (total statements)   -> 0 se 1
#   Chahiye: input, expected_output, retrieval_context
#   Low score = zaroori chunk miss ho gaya (top_k chota, embedding kamzor, waghera)
#
# ContextualPrecisionMetric  (retriever metric)
#   Sawal: "Kya RELEVANT chunks list ma UPAR (pehle rank pe) aaye?"
#   Kaise: judge har retrieved chunk ko relevant / irrelevant mark karta ha,
#          phir weighted precision nikalta ha -- relevant chunk jitna upar ho
#          utna behtar score. Irrelevant chunk top pe ho to score girta ha.
#   Chahiye: input, expected_output, retrieval_context
#   Low score = reranker sahi order nahi de raha / kachra upar aa raha ha
#
# Dono metrics ke common attributes (constructor arguments):
#   threshold      -> pass/fail ki line. score >= threshold = PASS (yahan 0.7)
#   model          -> judge LLM (hamara OllamaJudge). Na do to DeepEval
#                     default OpenAI model use karega.
#   include_reason -> True = judge score ke saath "kyun" bhi likhe (debug ke liye)
#   strict_mode    -> (optional) True = score sirf 0 ya 1, aur threshold 1 ho jata ha
#   async_mode     -> (optional, default True) metric ke andar judge calls async
#   verbose_mode   -> (optional) True = andar ke steps (statements, verdicts) print
# Run ke baad har metric object pe ye milte hain: .score, .reason, .success
# ---------------------------------------------------------

from harness import (
    load_goldens,
    summarize_by_metric,
    print_summary,
)


load_dotenv()

GOLDEN_PATH = "goldens/retriever_goldens.json"

# Judge model + Ollama URL ab judge.py / .env se aate hain

THRESHOLD = 0.7


print("========================================")
print("RETRIEVER EVALUATION STARTING")
print("========================================")


def run(retriever):

    # =====================================================
    # 1. LOAD GOLDEN SET
    # =====================================================

    goldens = load_goldens(GOLDEN_PATH)

    print(
        f"Loaded {len(goldens)} golden test cases "
        f"from {GOLDEN_PATH}"
    )


    # =====================================================
    # 2. RUN RETRIEVER
    # =====================================================

    test_cases = []

    for g in goldens:

        retrieved = retriever.invoke(g["query"])

        retrieval_context = [
            doc.page_content
            for doc in retrieved
        ]

        test_cases.append(
            LLMTestCase(
                input=g["query"],                       # sawal
                expected_output=g["ideal_answer"],      # golden sahi jawab (recall/precision isi se compare karte hain)
                retrieval_context=retrieval_context,    # retriever ke laaye hue chunks -- yahi asal mein test ho raha ha
                actual_output="(generator not evaluated in this run)",  # placeholder: retriever metrics isay use nahi karte
            )
        )


    # =====================================================
    # 3. OLLAMA JUDGE (shared, judge.py se)
    # =====================================================

    judge = get_judge()


    # =====================================================
    # 4. CREATE METRICS
    # =====================================================

    metrics = [

        ContextualRecallMetric(
            threshold=THRESHOLD,     # 0.7 se upar = PASS
            model=judge,             # OllamaJudge -- yahi LLM statements check karega
            include_reason=True,     # score ke saath wajah bhi
        ),

        ContextualPrecisionMetric(
            threshold=THRESHOLD,     # 0.7 se upar = PASS
            model=judge,             # same shared judge
            include_reason=True,     # kaunsa chunk irrelevant tha, reason ma batayega
        ),

    ]


    # =====================================================
    # 5. RUN DEEPEVAL
    # =====================================================

    result = evaluate(

        test_cases=test_cases,                        # kya check karna ha (LLMTestCase list)

        metrics=metrics,                              # kis pe check karna ha (recall + precision)

        async_config=AsyncConfig(max_concurrent=2),   # ek waqt ma sirf 2 test cases (Ollama overload na ho)

        hyperparameters={                             # sirf record ke liye -- score pe asar nahi

            "retriever": "reranker",

            "embedding_model": "openai/text-embedding-3-large",

            "chunk_size": 1000,

            "chunk_overlap": 150,

            "top_k": 3,

            "judge_provider": "ollama",

            "judge_model": JUDGE_MODEL,

            "golden_set": GOLDEN_PATH,

        },
    )
 

    # =====================================================
    # 6. SUMMARY
    # =====================================================

    return summarize_by_metric(result)


def run_local():
    """Standalone convenience: build the retriever, then run."""

    return run(
        RerankingRetriever()
    )


if __name__ == "__main__":

    print_summary(
        "retriever",
        run_local()
    )
