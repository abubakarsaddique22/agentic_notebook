import asyncio
import json
from datetime import datetime

from dotenv import load_dotenv

from src.generator import GENERATOR_MODEL, generate

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
from ragas.metrics.collections import AnswerRelevancy, Faithfulness
# ---------------------------------------------------------
# ragas.metrics.collections  (RAGAS 0.4 ke naye "modern" metrics)
#   Sab ka pattern ek jaisa:
#     metric = SomeMetric(llm=judge_llm, ...)          # judge CONSTRUCTOR ma
#     result = await metric.ascore(field1=..., ...)     # sirf zaroori fields
#     result.value  -> score (aksar 0.0 se 1.0, zyada = behtar)
#     result.reason -> wajah (har metric nahi deta)
#   harness.safe_score() yahi ascore() chalata ha aur error pe NaN deta ha.
#
# Faithfulness(llm)  -- hallucination check
#   ascore(user_input, response, retrieved_contexts)
#   Kaise: response ko chhote atomic statements ma todta ha, phir har statement
#          context ke against check (NLI): context se support hota ha ya nahi.
#   Score = supported statements / total statements
#   Low = model context se bahar ki baatein bana raha ha
#
# AnswerRelevancy(llm, embeddings, strictness=3)  -- on-topic check
#   ascore(user_input, response)   (context nahi chahiye)
#   Kaise: judge response se ULTA `strictness` (3) sawal banata ha ("ye jawab kis
#          sawal ka hoga?"), phir un sawalon ki asli sawal se cosine similarity
#          (embeddings se) nikal kar average. Gol-mol / "pata nahi" jawab = 0.
#   Is liye ise EMBEDDINGS bhi chahiye (judge.get_judge_embeddings).
#   Low = jawab sawal se hat kar ha
# ---------------------------------------------------------

from judge import get_judge_embeddings, get_judge_llm, judge_info
from harness import build_dataset, load_goldens, print_summary, safe_score

load_dotenv()

GOLDEN_PATH = "goldens/faithfulness_dataset.json"   # query + ideal_context (hand-picked chunks)
THRESHOLD = 0.7
MAX_CONCURRENT = 2

judge_llm = get_judge_llm()
judge_embeddings = get_judge_embeddings()

faithfulness = Faithfulness(llm=judge_llm)    # claims vs context -- sirf LLM chahiye
answer_relevancy = AnswerRelevancy(llm=judge_llm, embeddings=judge_embeddings)    # LLM (ulte sawal) + embeddings (cosine)

_slots = asyncio.Semaphore(MAX_CONCURRENT)


@experiment()    # is function ko RAGAS experiment bana do (.arun milega)
async def generator_experiment(row):
    context = json.loads(row["ideal_context"])        # CSV ma JSON string thi -> list

    async with _slots:
        # 1. GENERATE golden context pe (isolation)
        answer = await asyncio.to_thread(generate, row["query"], context)

        # 2. SCORE
        faith, faith_reason = await safe_score(
            faithfulness,
            user_input=row["query"],    # sawal (user_input)
            response=answer,    # bot ka jawab -- yahi judge hota ha
            retrieved_contexts=context,     # answer ko ISI context ke against check karo
        )
        relevancy, relevancy_reason = await safe_score(
            answer_relevancy,
            user_input=row["query"],    # sawal (user_input)
            response=answer,                # sirf question <-> answer, context nahi
        )

    return {
        **row,
        "answer": answer,
        "faithfulness": faith,
        "answer_relevancy": relevancy,
        "faithfulness_reason": faith_reason,
        "relevancy_reason": relevancy_reason,
        "generator_model": GENERATOR_MODEL,
        **judge_info(),
    }


async def main():
    goldens = load_goldens(GOLDEN_PATH)
    print(f"Loaded {len(goldens)} golden cases from {GOLDEN_PATH}")

    rows = [
        {
            "id": g["id"],
            "query": g["query"],
            "ideal_context": json.dumps(g["ideal_context"], ensure_ascii=False),
        }
        for g in goldens
    ]
    dataset = build_dataset("generator_goldens", rows)

    run_name = f"generator_{datetime.now():%Y%m%d-%H%M%S}"
    results = await generator_experiment.arun(dataset, name=run_name)    # har row pe chalao -> experiments/<run_name>.csv

    df = results.to_pandas()    # Experiment -> pandas DataFrame
    print_summary("generator (component level)", df,
                  ["faithfulness", "answer_relevancy"], THRESHOLD)
    print(f"\nPoori detail (answers + reasons): experiments/{run_name}.csv")


if __name__ == "__main__":
    asyncio.run(main())
