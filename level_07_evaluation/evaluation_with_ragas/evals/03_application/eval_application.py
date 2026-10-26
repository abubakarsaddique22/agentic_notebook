"""
APPLICATION LEVEL -- user ki nazar se (RAGAS)
=============================================

Pipeline level andar ka hisaab tha (context theek? grounded?). Application level pe
sirf ye dekhte hain ke STUDENT ko kya mila:

    1. Answer Accuracy  -- answer SAHI ha? (golden ideal_answer ke against)
                           RAGAS AnswerAccuracy: 2 judges 0/2/4 rating -> 0, 0.5, 1.
                           Extra sahi detail pe saza nahi deta (sirf galat/ulta pe).
    2. Completeness     -- ideal answer ke SAARE zaroori points cover hue?
                           RAGAS FactualCorrectness(mode="recall"):
                           ideal answer ke claims ma se kitne answer ma hain.
    3. Teaching Style   -- app ki apni requirement (generator prompt ke rules):
                           conversational prose, respectful, terms explain, no padding,
                           raw transcript dump nahi.  RAGAS DiscreteMetric (pass/fail).
    4. Latency          -- operational: har query ka time (p50 / p95).

Faithful != Correct: pipeline level pe answer context se grounded tha, lekin agar
retriever ne adhoora context diya to answer grounded hote hue bhi INCOMPLETE ho sakta ha.
Isi liye yahan golden answer (reference) ke against check karte hain.

Run (project root se):
    python -m evals.03_application.eval_application
"""

import asyncio
import time
from datetime import datetime

from dotenv import load_dotenv

from src.rag_pipeline import RagPipeline
from src.generator import GENERATOR_MODEL

from ragas import experiment
# ---------------------------------------------------------
# experiment  (decorator)  -- RAGAS ka "run button" (DeepEval ke evaluate() jaisa)
#   @experiment() ek async function pe lagta ha jo EK row (dict) leta ha aur
#   result ka dict wapas karta ha. Decorator us function ko ExperimentWrapper
#   bana deta ha, jis pe .arun() milta ha.
#
#   @experiment(...) ke arguments (sab optional):
#     experiment_model -> pydantic model: har result row isi shape ma validate ho
#     backend          -> results kahan save hon (warna dataset wala backend)
#     name_prefix      -> har experiment naam ke aage lagne wala prefix
#
#   await my_experiment.arun(dataset, name="..."):
#     - dataset ki HAR row pe function chalata ha -- sab rows EK SAATH (asyncio).
#       RAGAS khud koi concurrency limit nahi lagata, isi liye hum apna
#       asyncio.Semaphore (_slots) use karte hain, warna Ollama pe 429 aata ha.
#     - koi row crash ho to "Warning: Task failed with error" print, row result
#       se GAYAB (is liye kuch files row ke andar try/except lagati hain)
#     - results experiments/<name>.csv ma save (local/csv backend)
#     - return: Experiment object -> .to_pandas() se DataFrame
#   NOTE: DeepEval ki tarah threshold / pass-fail RAGAS nahi lagata -- wo hum
#   khud harness.print_summary() ma THRESHOLD se karte hain.
# ---------------------------------------------------------
from ragas.metrics import DiscreteMetric
# ---------------------------------------------------------
# DiscreteMetric  (custom LLM-judge metric -- DeepEval ke GEval jaisa)
#   Jab built-in metric kaafi na ho, apna prompt likh kar judge bana lo jo
#   sirf DIYE GAYE categories ma se ek jawab de.
#   Attributes (constructor):
#     name           -> metric ka naam (result/CSV ma)
#     allowed_values -> judge sirf inhi ma se ek value de sakta ha
#                       (default ["pass", "fail"]; yahan ANSWER/DECLINE/PARTIAL bhi)
#     prompt         -> judge ka prompt; {user_input}, {response} jaise
#                       placeholders run time pe bharte hain
#   Score kaise:
#     result = await metric.ascore(llm=judge_llm, user_input=..., response=...)
#     -> llm HAR CALL pe dena hota ha (collections metrics ki tarah constructor
#        ma nahi), aur baqi kwargs ke naam prompt ke {placeholders} se match hon.
#     result.value  -> allowed_values ma se ek (jaise "pass")
#     result.reason -> judge ki wajah
#   harness.to_float() "pass"/"fail" ko 1.0 / 0.0 bana deta ha.
#   (Isi family ma NumericMetric aur RankingMetric bhi hain.)
# ---------------------------------------------------------
from ragas.metrics.collections import AnswerAccuracy, FactualCorrectness
# ---------------------------------------------------------
# ragas.metrics.collections  (RAGAS 0.4 ke naye "modern" metrics)
#   Sab ka pattern ek jaisa:
#     metric = SomeMetric(llm=judge_llm, ...)          # judge CONSTRUCTOR ma
#     result = await metric.ascore(field1=..., ...)     # sirf zaroori fields
#     result.value  -> score (aksar 0.0 se 1.0, zyada = behtar)
#     result.reason -> wajah (har metric nahi deta)
#   harness.safe_score() yahi ascore() chalata ha aur error pe NaN deta ha.
#
# AnswerAccuracy(llm)  -- jawab SAHI ha? (reference ke against)
#   ascore(user_input, response, reference)
#   Kaise: DO judge prompts (NVIDIA dual-judge, doosre ma perspective ulta)
#          0 / 2 / 4 rating dete hain (match nahi / thora / poora). Average -> 0, 0.5, 1.
#   Extra sahi detail pe saza nahi -- sirf galat ya ulti baat pe.
#
# FactualCorrectness(llm, mode="f1", beta=1.0, atomicity="low", coverage="low")
#   ascore(response, reference)   (user_input nahi chahiye)
#   Kaise: response aur reference dono ko claims ma todta ha, phir NLI se check.
#   mode:
#     "precision" -> response ke claims ma se kitne reference se support (sach?)
#     "recall"    -> reference ke claims ma se kitne response ma aaye (POORA?)
#                    <- yahan yahi use ho raha ha = COMPLETENESS
#     "f1"        -> dono ka harmonic mean (beta se weight)
#   atomicity / coverage -> "high" = zyada chhote aur zyada claims (sakht, mehnga)
# ---------------------------------------------------------

from judge import get_judge_llm, judge_info
from harness import build_dataset, load_goldens, print_latency, print_summary, safe_score

load_dotenv()

GOLDEN_PATH = "goldens/correctness_goldens.json"   # question + ideal_answer
THRESHOLD = 0.7
MAX_CONCURRENT = 2

# ---------------------------------------------------------
# ek dafa banao
# ---------------------------------------------------------
rag = RagPipeline()
judge_llm = get_judge_llm()

answer_accuracy = AnswerAccuracy(llm=judge_llm)    # dual judge 0/2/4 -> 0..1
completeness = FactualCorrectness(llm=judge_llm, mode="recall")    # recall = reference ke claims kitne cover hue

teaching_style = DiscreteMetric(
    name="teaching_style",    # metric ka naam (CSV / result ma)
    allowed_values=["pass", "fail"],    # judge sirf inhi ma se ek value dega
    prompt="""You are checking whether a course teaching-assistant's answer follows the app's style rules.

Rules the answer MUST follow:
1. Written as flowing, conversational prose like a teacher explaining out loud. A list is allowed ONLY if the question genuinely asks to enumerate things.
2. Respectful, professional tone. No mocking, insulting or toxic language.
3. Any technical term it uses is briefly explained in plain language.
4. No padding: no unrelated information, no repeating the same point.
5. It must NOT dump raw lecture transcript text (long verbatim, messy spoken-style passages).

If the answer is exactly "I don't have enough information in the course material to answer that." then it passes the style check.

Student question:
{user_input}

Answer:
{response}

Return "pass" if ALL rules are followed, otherwise "fail". In the reason, name the rule numbers that were broken.""",
)

_slots = asyncio.Semaphore(MAX_CONCURRENT)


@experiment()    # is function ko RAGAS experiment bana do (.arun milega)
async def application_experiment(row):
    async with _slots:
        # 1. User ka sawal -> poora app (jaise asli student use karega)
        t0 = time.perf_counter()
        out = await asyncio.to_thread(rag.invoke, row["query"])
        latency = time.perf_counter() - t0
        answer = out["answer"]

        # 2. CORRECTNESS (reference ke against)
        acc, acc_reason = await safe_score(
            answer_accuracy,
            user_input=row["query"],    # sawal (user_input)
            response=answer,    # bot ka jawab -- yahi judge hota ha
            reference=row["ideal_answer"],    # golden / ideal jawab
        )

        # 3. COMPLETENESS (reference ke kitne points answer ma aaye)
        comp, comp_reason = await safe_score(
            completeness,
            response=answer,    # bot ka jawab -- yahi judge hota ha
            reference=row["ideal_answer"],    # golden / ideal jawab
        )

        # 4. TEACHING STYLE (app requirement, pass/fail -> 1.0/0.0)
        style, style_reason = await safe_score(
            teaching_style,
            llm=judge_llm,                 # DiscreteMetric ko llm har call pe dena hota ha
            user_input=row["query"],    # sawal (user_input)
            response=answer,    # bot ka jawab -- yahi judge hota ha
        )

    return {
        **row,
        "answer": answer,
        "answer_accuracy": acc,
        "completeness": comp,
        "teaching_style": style,
        "latency_s": round(latency, 2),
        "answer_words": len(answer.split()),
        "accuracy_reason": acc_reason,
        "completeness_reason": comp_reason,
        "style_reason": style_reason,
        "generator_model": GENERATOR_MODEL,
        **judge_info(),
    }


async def main():
    goldens = load_goldens(GOLDEN_PATH)
    print(f"Loaded {len(goldens)} golden cases from {GOLDEN_PATH}")

    rows = [
        {"id": g["id"], "query": g["question"], "ideal_answer": g["ideal_answer"]}
        for g in goldens
    ]
    dataset = build_dataset("application_goldens", rows)

    run_name = f"application_{datetime.now():%Y%m%d-%H%M%S}"
    results = await application_experiment.arun(dataset, name=run_name)    # har row pe chalao -> experiments/<run_name>.csv

    df = results.to_pandas()    # Experiment -> pandas DataFrame
    print_summary("application (user perspective)", df,
                  ["answer_accuracy", "completeness", "teaching_style"], THRESHOLD)
    print_latency(df)
    words = df["answer_words"].astype(float)
    print(f"ANSWER LENGTH: avg {words.mean():.0f} words, max {words.max():.0f}")
    print(f"\nPoori detail (answers + reasons): experiments/{run_name}.csv")


if __name__ == "__main__":
    asyncio.run(main())
