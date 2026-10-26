"""
evals/03_application/eval_citation.py
=====================================
Application-level eval: CITATION BEHAVIOUR.

Roadmap M7.8 (application level): "tone, format & citation behaviour".
Student ko pata hona chahiye ke jawab kis session se aaya, aur woh citation
SACHI honi chahiye.

App side (src/):
    RagPipeline.invoke_with_citations(query)
      -> har chunk ke aage "[Session N]" label
      -> generator har claim ke baad [Session N] lagata ha

4 metrics -- 3 programmatic (programmatic.py) + 1 LLM judge:

    Citation Presence      (code)  answer ma kam az kam ek [Session N] ha?
                                   (abstain answer pe citation nahi chahiye)
    Citation Validity      (code)  har cited session retrieved context ma tha?
                                   (warna = invented / hallucinated citation)
    Citation Source Match  (code)  golden ka expected session cite hua?
                                   reason batata ha RETRIEVAL MISS ya GENERATOR MISS
    Citation Faithfulness  (GEval) jo claim [Session N] ke saath likha, kya wo
                                   ussi session ke chunk ma likha ha?

Golden set: goldens/correctness_goldens.json  (question + source_session, e.g. "S2-S3")

Run (project root se):
    python -m evals.03_application.eval_citation
"""

print("[1] eval_citation.py started")

# ---------------------------------------------------------
# IMPORT ORDER (Windows): src.* -> judge -> deepeval
# ---------------------------------------------------------
from src.rag_pipeline import RagPipeline

print("[2] pipeline imported")

from judge import get_judge, JUDGE_MODEL   # shared Ollama judge (project root)
from programmatic import (                 # shared programmatic metrics (project root)
    CitationPresenceMetric,
    CitationValidityMetric,
    CitationSourceMatchMetric,
    cited_sessions,
)
from harness import load_goldens, summarize_by_metric, print_summary

import re

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
#   Yahan: name (golden id), input, actual_output, retrieval_context ("[Session N]"
#   labeled chunks) aur additional_metadata (retrieved / expected sessions --
#   programmatic citation metrics isi se parhte hain).
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

print("[3] deepeval imported")

load_dotenv()

GOLDEN_PATH = "goldens/correctness_goldens.json"
THRESHOLD = 0.7
MAX_CONCURRENT = 1                            # 1 = sab se stable, 2 = tez lekin risky


# =========================================================
# HELPERS
# =========================================================

def parse_sessions(source_session: str) -> list[str]:
    """'S2' -> ['2'],  'S2-S3' -> ['2','3'],  'S4-S6' -> ['4','5','6']"""
    nums = [int(n) for n in re.findall(r"\d+", source_session or "")]
    if len(nums) == 2 and "-" in source_session:
        lo, hi = sorted(nums)
        return [str(n) for n in range(lo, hi + 1)]
    return [str(n) for n in nums]


def print_case_table(result, test_cases):
    test_results = getattr(result, "test_results", None) or []
    # DeepEval ka TestResult additional_metadata wapas nahi deta -> name se apne test case dhoondo
    by_name = {tc.name: tc for tc in test_cases}

    print("\n" + "=" * 100)
    print("CITATIONS  (per-case recap)")
    print("=" * 100)
    print(f"{'case':<6} {'expected':<10} {'retrieved':<16} {'cited':<14} {'present':<8} {'valid':<6} {'match':<6} faithful")
    print("-" * 100)

    for tr in test_results:
        m = {getattr(x, "name", ""): x for x in (getattr(tr, "metrics_data", None) or [])}
        tc = by_name.get(getattr(tr, "name", None))
        md = (tc.additional_metadata if tc else None) or {}

        def pf(name):
            x = m.get(name)
            return "n/a" if x is None else ("PASS" if x.success else "FAIL")

        faith = next((x for n, x in m.items() if n.startswith("Citation Faithfulness")), None)
        faith_txt = "n/a" if faith is None or faith.score is None else f"{faith.score:.2f} {'P' if faith.success else 'F'}"

        cited = ",".join(cited_sessions(getattr(tr, "actual_output", "") or "")) or "-"
        print(f"{getattr(tr, 'name', '?'):<6} "
              f"{','.join(md.get('expected_sessions', [])):<10} "
              f"{','.join(sorted(set(md.get('retrieved_sessions', [])))):<16} "
              f"{cited:<14} {pf('Citation Presence'):<8} {pf('Citation Validity'):<6} "
              f"{pf('Citation Source Match'):<6} {faith_txt}")

    print("=" * 100)
    print("match FAIL ka reason DeepEval report ma dekho: RETRIEVAL MISS = retriever ki ghalti,")
    print("GENERATOR MISS = sahi session mila tha lekin cite nahi kiya.")


# =========================================================
# EVAL
# =========================================================

def run(rag=None):
    # 1. LOAD goldens (question + source_session)
    goldens = load_goldens(GOLDEN_PATH)
    print(f"Loaded {len(goldens)} golden questions from {GOLDEN_PATH}")

    # 2. RUN the CITED pipeline per question
    rag = rag or RagPipeline()
    test_cases = []

    for g in goldens:
        result = rag.invoke_with_citations(g["question"])

        test_cases.append(
            LLMTestCase(
                name=g["id"],    # test case ka id (report ma pehchan)
                input=g["question"],    # sawal / user message
                actual_output=result["answer"],    # bot ka jawab -- yahi test ho raha ha
                retrieval_context=result["context"],      # "[Session N] text" labeled chunks
                additional_metadata={    # apna extra data -- programmatic metrics yahan se parhte hain
                    "retrieved_sessions": result["sessions"],
                    "expected_sessions": parse_sessions(g.get("source_session", "")),
                },
            )
        )

    # 3. JUDGE: sirf ek dafa, loop ke BAHAR
    judge = get_judge()

    # 4a. CITATION FAITHFULNESS --- LLM judge (GEval)
    citation_faithfulness = GEval(
        name="Citation Faithfulness",    # metric ka naam (report ma yahi dikhega)
        evaluation_steps=[    # judge ke apne steps (diye hain to auto-CoT skip)
            "Each chunk in the retrieval context starts with a label like [Session 3]. The actual output cites sources using the same [Session N] labels.",
            "For every sentence in the actual output that carries a [Session N] citation, check whether the cited chunk(s) with that label actually support that sentence.",
            "A citation is wrong if the cited session's chunk does not contain the information, or if the claim actually comes from a different session's chunk.",
            "Sentences without a citation are not judged here. Do NOT judge correctness against outside knowledge, completeness, length, or style -- only whether the citations point to supporting chunks.",
            "If the actual output abstains and contains no citations, give a full score.",
        ],
        rubric=[    # kis score range ka kya matlab
            Rubric(score_range=(9, 10), expected_outcome="Every cited claim is supported by the chunk carrying that session label."),
            Rubric(score_range=(5, 8),  expected_outcome="Most citations are supported, but one or two point to the wrong session or only weakly support the claim."),
            Rubric(score_range=(0, 4),  expected_outcome="Many citations point to sessions that do not support the claim, or citations look arbitrary."),
        ],
        evaluation_params=[    # judge ko test case ke SIRF ye fields dikhenge
            LLMTestCaseParams.ACTUAL_OUTPUT,
            LLMTestCaseParams.RETRIEVAL_CONTEXT,
        ],
        threshold=THRESHOLD,    # score >= threshold = PASS
        model=judge,    # judge LLM (OllamaJudge) jo score dega
        strict_mode=False,    # False = 0..1 ka score (True = sirf 0 ya 1)
    )

    # 4b. PROGRAMMATIC --- no judge
    metrics = [
        CitationPresenceMetric(),
        CitationValidityMetric(),
        CitationSourceMatchMetric(),
        citation_faithfulness,
    ]

    # 5. EVALUATE
    result = evaluate(
        test_cases=test_cases,    # kya check karna ha (LLMTestCase list)
        metrics=metrics,    # kin metrics pe check karna ha
        async_config=AsyncConfig(max_concurrent=MAX_CONCURRENT),    # ek waqt ma MAX_CONCURRENT test cases
        hyperparameters={    # sirf record ke liye -- score pe asar nahi
            "eval": "citation",
            "fetch_k": rag.retriever.fetch_k,
            "top_k": rag.retriever.top_k,
            "judge_model": JUDGE_MODEL,
            "golden_set": GOLDEN_PATH,
        },
    )

    print_case_table(result, test_cases)
    return summarize_by_metric(result)


if __name__ == "__main__":
    print_summary("citation", run())
