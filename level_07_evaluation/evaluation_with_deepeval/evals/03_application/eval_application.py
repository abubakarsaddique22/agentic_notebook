"""
evals/eval_application.py
=========================
Application-level quality eval of the WHOLE RAG pipeline using GEval:

    Correctness  : reference-based, sirf TRUTH judge karta ha
    Completeness : reference-based, sirf COVERAGE judge karta ha
    Style        : reference-free, sirf TONE judge karta ha

Setup (one time):
    pip install json-repair
    ollama signin

Run:
    python -m evals.eval_application
"""

print("[1] eval_application.py started")

# DEEPEVAL TIMEOUTS ab judge.py ma set hote hain (judge deepeval se PEHLE import hota ha)

# ---------------------------------------------------------
# IMPORT ORDER MATTERS (Windows):
# src.* (reranker -> torch / chroma) deepeval / openai se PEHLE import karo,
# warna DLL conflict se process bina error ke chup-chaap exit ho sakta ha.
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
from deepeval.test_case import LLMTestCase, LLMTestCaseParams
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
#   Yahan: input + actual_output + expected_output (ideal_answer). Correctness
#   aur Completeness ko expected_output chahiye, Style ko nahi.
# ---------------------------------------------------------
# ---------------------------------------------------------
# LLMTestCaseParams  (Enum -- fields ke naam)
#   GEval ko batata ha ke judge ko test case ke KAUNSE fields dikhane hain.
#   Jo field list ma nahi, judge us ko dekhta hi nahi.
#     INPUT             -> sawal
#     ACTUAL_OUTPUT     -> bot ka jawab
#     EXPECTED_OUTPUT   -> golden jawab / expected behaviour
#     RETRIEVAL_CONTEXT -> retrieved chunks
#     CONTEXT           -> ideal context (yahan use nahi)
#     TOOLS_CALLED      -> agent ne jo tools call kiye (agent eval ma)
#     EXPECTED_TOOLS    -> jo tools call hone chahiye the
#   (naye DeepEval 4.x ma iska naam SingleTurnParams ha, purana naam bhi chalta ha)
# ---------------------------------------------------------
from deepeval.metrics import GEval
# ---------------------------------------------------------
# GEval  (custom LLM-judge metric -- "apna metric khud likho")
#   Jab built-in metric (Faithfulness waghera) aap ki zaroorat poori na kare,
#   GEval ma aap angrezi ma likh do ke judge kya check kare. Judge 0-10 score
#   deta ha, DeepEval usay 0-1 pe le aata ha (score / 10).
#   Attributes (constructor arguments):
#     name              -> metric ka naam (report/table ma yahi dikhta ha)
#     criteria          -> (optional) ek line ma kya judge karna ha. Agar sirf
#                          criteria do to DeepEval khud CoT se steps bana leta ha.
#     evaluation_steps  -> aap ke apne steps (list). Ye do to auto steps wala
#                          CoT skip ho jata ha -- zyada control, kam randomness.
#                          criteria YA evaluation_steps -- dono mein se ek zaroori.
#     rubric            -> Rubric objects ki list: kis score range ka kya matlab
#     evaluation_params -> LLMTestCaseParams ki list: judge ko kaunse fields dikhein
#     threshold         -> score >= threshold = PASS
#     model             -> judge LLM (hamara OllamaJudge)
#     strict_mode       -> True = score sirf 0 ya 1 (pass/fail)
#     async_mode        -> (optional, default True) judge calls async
#     verbose_mode      -> (optional) andar ke steps print kare
# ---------------------------------------------------------
from deepeval.metrics.g_eval import Rubric
# ---------------------------------------------------------
# Rubric  (GEval ke liye score guide)
#   Judge ko batata ha ke kis score range ka kya matlab ha, taake score
#   consistent rahe (warna judge apni marzi se 6 ya 7 de deta ha).
#     score_range      -> (min, max) tuple, 0 se 10 ke beech, dono inclusive.
#                         Ranges aapas ma overlap nahi kar sakti.
#     expected_outcome -> us range ma jawab kaisa hona chahiye (plain angrezi)
# ---------------------------------------------------------

from harness import load_goldens, summarize_by_metric, print_summary

print("[3] deepeval imported")

load_dotenv()

GOLDEN_PATH = "goldens/correctness_goldens.json"
THRESHOLD = 0.7
MAX_CONCURRENT = 1                            # 1 = sab se stable, 2 = tez lekin risky


# =========================================================
# EVAL
# =========================================================

def run(rag):
    # 1. LOAD queries + ideal answers
    goldens = load_goldens(GOLDEN_PATH)
    print(f"Loaded {len(goldens)} golden test cases from {GOLDEN_PATH}")

    # 2. RUN THE PIPELINE per query, LIVE output se test case banao
    test_cases = []
    for g in goldens:
        result = rag.invoke(g["question"])          # retrieve -> rerank -> generate

        test_cases.append(
            LLMTestCase(
                input=g["question"],    # sawal / user message
                actual_output=result["answer"],    # bot ka jawab -- yahi test ho raha ha
                expected_output=g["ideal_answer"],    # golden: ideal jawab / expected behaviour
            )
        )

    # 3. JUDGE: sirf ek dafa, loop ke BAHAR
    judge = get_judge()

    # 4. THREE APPLICATION-LEVEL QUALITY METRICS

    # 4a. CORRECTNESS --- reference-based, judges TRUTH (not coverage or length)
    correctness = GEval(
        name="Correctness",    # metric ka naam (report ma yahi dikhega)
        evaluation_steps=[ # jaha pa hum saii tara define kar raha hai tu ab cot skip ho jaa gaa agr hight level hotaa tu phir cot deepeval kuhd step karta
            "Compare only the factual claims in the actual output against the expected output.",
            "A claim is wrong only if it CONTRADICTS the expected output or is factually false. Judge truth, not completeness.",
            "A factually accurate answer must score at least 0.9 even if it is shorter or covers fewer points than the expected output.",
            "Do NOT deduct for brevity, missing elaboration, or omitted points --- omissions are not errors here.",
            "Additional correct information must NEVER lower the score.",
        ],
        rubric=[ # rubric define karta ha ki kis range ma kya outcome expect hota ha
            Rubric(score_range=(9, 10), expected_outcome="All stated claims are factually correct and consistent. No contradictions. Brevity is fine."),
            Rubric(score_range=(5, 8),  expected_outcome="Mostly correct but one minor inaccuracy."),
            Rubric(score_range=(0, 4),  expected_outcome="Contains a clear factual error or a claim that contradicts the expected output."),
        ],
        evaluation_params=[LLMTestCaseParams.INPUT, LLMTestCaseParams.ACTUAL_OUTPUT, LLMTestCaseParams.EXPECTED_OUTPUT],    # judge ko sawal + jawab + golden dikhao
        threshold=THRESHOLD,    # score >= threshold = PASS
        model=judge,    # judge LLM (OllamaJudge) jo score dega
        strict_mode=False,    # False = 0..1 ka score (True = sirf 0 ya 1)
    )

    # 4b. COMPLETENESS --- reference-based, judges COVERAGE (not correctness)
    completeness = GEval(
        name="Completeness",    # metric ka naam (report ma yahi dikhega)
        evaluation_steps=[     # judge ke apne steps (diye hain to auto-CoT skip)
            "Identify the key points contained in the expected output.",
            "Check how many of those key points are addressed in the actual output.",
            "Penalize the actual output for each key point from the expected output that it omits or only partially covers.",
            "Judge coverage only. Do NOT lower the score because a covered point is stated incorrectly --- factual correctness is judged separately.",
            "Do NOT penalize the actual output for adding extra information beyond the expected output.",
        ],
        rubric=[    # kis score range ka kya matlab
            Rubric(score_range=(9, 10), expected_outcome="Addresses essentially all key points in the expected output."),
            Rubric(score_range=(5, 8),  expected_outcome="Covers the main key points but misses one or more."),
            Rubric(score_range=(0, 4),  expected_outcome="Misses several key points; only partially covers the expected output."),
        ],
        evaluation_params=[LLMTestCaseParams.INPUT, LLMTestCaseParams.ACTUAL_OUTPUT, LLMTestCaseParams.EXPECTED_OUTPUT],    # judge ko sawal + jawab + golden dikhao
        threshold=THRESHOLD,    # score >= threshold = PASS
        model=judge,    # judge LLM (OllamaJudge) jo score dega
        strict_mode=False,    # False = 0..1 ka score (True = sirf 0 ya 1)
    )

    # 4c. STYLE --- reference-free, judges TONE only (note: no EXPECTED_OUTPUT)
    style = GEval(
        name="Style",    # metric ka naam (report ma yahi dikhega)
        evaluation_steps=[    # judge ke apne steps (diye hain to auto-CoT skip)
            "Judge only the teaching style and tone of the actual output, not whether it is factually correct or complete.",
            "Reward an intuitive, explanatory tone: plain language, the idea explained before any formula or jargon, and technical terms briefly unpacked when used.",
            "Reward a direct, conversational register written in prose, as a CampusX lecture would explain it out loud, rather than a dry, formal, or bullet-list tone.",
            "An analogy or concrete example is a BONUS when the concept is abstract, but a clear, direct, well-explained answer is fully acceptable and must NOT be penalized for not having one.",
            "Penalize answers that are stiff, bureaucratic, structured as a bare list with no explanation, or that use unexplained jargon.",
            "Do NOT reward or penalize based on correctness, completeness, or length --- only on style and tone.",
        ],
        rubric=[    # kis score range ka kya matlab
            Rubric(score_range=(9, 10), expected_outcome="Clearly in a CampusX teaching voice: intuitive, conversational prose that explains before it formalizes."),
            Rubric(score_range=(7, 8),  expected_outcome="Clear, conversational, and well-explained in prose. Fully acceptable even without an analogy or example."),
            Rubric(score_range=(4, 6),  expected_outcome="Understandable but somewhat flat, formal, or list-heavy in places."),
            Rubric(score_range=(0, 3),  expected_outcome="Dry, stiff, bare-list, jargon-heavy, or robotic; does not read like a teaching explanation."),
        ],
        evaluation_params=[LLMTestCaseParams.INPUT, LLMTestCaseParams.ACTUAL_OUTPUT],    # reference-free: expected_output nahi dikhaya
        threshold=THRESHOLD,    # score >= threshold = PASS
        model=judge,    # judge LLM (OllamaJudge) jo score dega
        strict_mode=False,    # False = 0..1 ka score (True = sirf 0 ya 1)
    )

    # 5. EVALUATE --- teeno saath ma
    result = evaluate(
        test_cases=test_cases,    # kya check karna ha (LLMTestCase list)
        metrics=[correctness, completeness, style],    # kin metrics pe check karna ha
        async_config=AsyncConfig(max_concurrent=MAX_CONCURRENT),    # ek waqt ma MAX_CONCURRENT test cases
    )
    return summarize_by_metric(result)


def run_local():
    """Standalone convenience: pipeline banao, phir run karo."""
    return run(RagPipeline())


if __name__ == "__main__":
    print_summary("application", run_local())