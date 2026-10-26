from dotenv import load_dotenv

# IMPORT ORDER (Windows): src.* -> judge -> deepeval
from src.generator import generate   # generate(query, context) -> answer

from judge import get_judge          # shared Ollama judge (project root)

from deepeval import evaluate
# ---------------------------------------------------------
# evaluate  (function)
#   DeepEval ka main runner. test_cases + metrics leta ha, har test case pe
#   har metric chalata ha (judge LLM ke zariye), score/reason nikalta ha,
#   table print karta ha aur EvaluationResult wapas deta ha.
#   Arguments:
#     test_cases   -> LLMTestCase ki list
#     metrics      -> metrics ki list
#     async_config -> parallelism settings (AsyncConfig)
#   Return: EvaluationResult -> .test_results -> har ek ka .metrics_data
#           (name, score, success, reason). summarize_by_metric() isay parhta ha.
# ---------------------------------------------------------

from deepeval.evaluate.configs import AsyncConfig
# ---------------------------------------------------------
# AsyncConfig  (settings class)
#   evaluate() ko batata ha test cases kitne parallel chalein.
#     run_async      -> True (default) = async, False = sequential
#     max_concurrent -> ek waqt ma kitne test cases (yahan MAX_CONCURRENT = 1)
#     throttle_value -> har test case se pehle kitne second ka wait (default 0)
#   Ye sirf test-case level limit ha; judge calls ki asli limit judge.py ka
#   semaphore lagata ha.
# ---------------------------------------------------------

from deepeval.test_case import LLMTestCase
# ---------------------------------------------------------
# LLMTestCase  (data container class)
#   Ek sawal ka poora data jo metrics parhte hain.
#     input             -> user ka sawal
#     actual_output     -> generator ka jawab (yahi test ho raha ha)
#     retrieval_context -> wo chunks jo generator ko diye gaye (yahan golden
#                          ideal_context -- taake retriever ki ghalti beech
#                          ma na aaye, sirf generator isolate ho)
#     expected_output   -> (optional) yahan zaroorat nahi, in dono metrics ko
#                          ideal answer nahi chahiye
# ---------------------------------------------------------

from deepeval.metrics import FaithfulnessMetric, AnswerRelevancyMetric
# ---------------------------------------------------------
# FaithfulnessMetric  (generator metric -- hallucination check)
#   Sawal: "Kya jawab ki har baat diye gaye context se SABIT hoti ha?"
#   Kaise: judge actual_output se claims nikalta ha, retrieval_context se
#          facts (truths) nikalta ha, phir har claim check karta ha ke context
#          use contradict to nahi karta.
#   Score = (wo claims jo context ke khilaf nahi) / (total claims)  -> 0 se 1
#   Chahiye: input, actual_output, retrieval_context
#   Low score = model apni taraf se baatein bana raha ha (hallucination)
#
# AnswerRelevancyMetric  (generator metric -- on-topic check)
#   Sawal: "Kya jawab ASAL sawal ka hi jawab ha, ya idhar udhar ki baatein?"
#   Kaise: judge actual_output ko statements ma todta ha aur har statement
#          ko input (sawal) ke against relevant / irrelevant mark karta ha.
#   Score = (relevant statements) / (total statements)  -> 0 se 1
#   Chahiye: input, actual_output   (context nahi chahiye)
#   Low score = jawab lamba aur off-topic, ya sawal ko miss kar gaya
#
# Common attributes (dono metrics):
#   threshold      -> score >= threshold = PASS (yahan 0.7)
#   model          -> judge LLM (OllamaJudge). Na do to default OpenAI model
#   include_reason -> True = score ki wajah bhi likhe
#   strict_mode    -> (optional) sirf 0/1 score
#   async_mode     -> (optional, default True) andar ki judge calls async
#   verbose_mode   -> (optional) andar ke steps print kare
#   FaithfulnessMetric extra: truths_extraction_limit -> context se zyada se
#                     zyada kitne facts nikale (bara context ho to useful)
# Run ke baad: metric.score, metric.reason, metric.success
# ---------------------------------------------------------

from harness import load_goldens, summarize_by_metric, print_summary

load_dotenv()

GOLDEN_PATH = "goldens/faithfulness_dataset.json"
THRESHOLD = 0.7
MAX_CONCURRENT = 1                            # 1 = sab se stable, 2 = tez lekin risky


# =========================================================
# EVAL
# =========================================================

def run():
    # 1. LOAD golden set (query + ideal_context)
    goldens = load_goldens(GOLDEN_PATH)
    print(f"Loaded {len(goldens)} golden test cases from {GOLDEN_PATH}")

    # 2. RUN GENERATOR on GOLDEN context (isolation), one test case each
    test_cases = []
    for g in goldens:
        context = g["ideal_context"]              # list of chunk strings
        answer = generate(g["query"], context)    # actual_output

        test_cases.append(
            LLMTestCase(
                input=g["query"],                 # sawal (answer relevancy isi se compare karta ha)
                actual_output=answer,             # generator ka jawab -- yahi test ho raha ha
                retrieval_context=context,        # faithfulness answer ko isi se check karta ha
            )
        )

    # 3. JUDGE: sirf ek dafa, loop ke BAHAR
    judge = get_judge()

    # 4. METRICS
    metrics = [
        # threshold=0.7 pass line | model=judge (Ollama) | include_reason=True -> wajah bhi
        FaithfulnessMetric(threshold=THRESHOLD, model=judge, include_reason=True),     # context se sach ha?
        AnswerRelevancyMetric(threshold=THRESHOLD, model=judge, include_reason=True),  # sawal ka hi jawab ha?
    ]

    # 5. EVALUATE
    result = evaluate(
        test_cases=test_cases,                                      # kya check karna ha
        metrics=metrics,                                            # kin metrics pe
        async_config=AsyncConfig(max_concurrent=MAX_CONCURRENT),    # ek waqt ma 1 test case
    )
    return summarize_by_metric(result)


if __name__ == "__main__":
    print_summary("generator", run())