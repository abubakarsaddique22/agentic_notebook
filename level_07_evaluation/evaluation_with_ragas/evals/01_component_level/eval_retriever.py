"""
COMPONENT LEVEL -- 1. RETRIEVER eval (RAGAS)
============================================

Retriever ko ISOLATION ma test karte hain: sirf query do, jo chunks aaye unhe judge karo.
Generator is run ma involved hi nahi.

Retriever ke 2 failure modes -> 2 metrics:
    1. Sahi context miss kar diya    -> ContextRecall
         ideal answer (reference) ko claims ma todo, dekho kitne claims
         retrieved chunks se support hote hain.
    2. Sahi ke saath noise bhi laaya -> ContextPrecision
         har chunk relevant hai ya nahi + RANK-AWARE (sahi chunks upar hon to zyada score).

Dono REFERENCE-BASED hain -> golden dataset: query + ideal_answer (chunk IDs nahi,
taake chunk size/overlap badalne pe dataset invalid na ho).

Run (project root se):
    python -m evals.01_component_level.eval_retriever

Results: experiments/<naam>.csv  (RAGAS khud save karta ha)
"""

import asyncio
from datetime import datetime

from dotenv import load_dotenv

from src.reranker import RerankingRetriever

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
from ragas.metrics.collections import ContextPrecision, ContextRecall
# ---------------------------------------------------------
# ragas.metrics.collections  (RAGAS 0.4 ke naye "modern" metrics)
#   Sab ka pattern ek jaisa:
#     metric = SomeMetric(llm=judge_llm, ...)          # judge CONSTRUCTOR ma
#     result = await metric.ascore(field1=..., ...)     # sirf zaroori fields
#     result.value  -> score (aksar 0.0 se 1.0, zyada = behtar)
#     result.reason -> wajah (har metric nahi deta)
#   harness.safe_score() yahi ascore() chalata ha aur error pe NaN deta ha.
#
# ContextRecall(llm)  -- kuch zaroori MISS to nahi hua? (retriever)
#   ascore(user_input, retrieved_contexts, reference)
#   Kaise: reference (ideal answer) ko claims ma todta ha, phir har claim:
#          kya retrieved context se attribute hota ha? (1/0)
#   Score = attributed claims / total claims
#   Low = sahi chunk aaya hi nahi (fetch_k / top_k / embedding model)
#
# ContextPrecision(llm)  -- RANK-AWARE noise check (retriever)
#   ascore(user_input, reference, retrieved_contexts)
#   Kaise: har chunk pe judge verdict: is chunk ne reference (ideal answer)
#          tak pohanchne ma madad ki? (1/0). Phir average precision: relevant
#          chunks jitne UPAR hon utna zyada score.
#   Low = kachra chunks upar aa rahe hain (reranker / top_k dekho)
#
# Dono REFERENCE-BASED: reference = golden ideal_answer chahiye.
# ---------------------------------------------------------

from judge import get_judge_llm, judge_info
from harness import build_dataset, load_goldens, print_summary, safe_score

load_dotenv()

GOLDEN_PATH = "goldens/retriever_goldens.json"
THRESHOLD = 0.7
MAX_CONCURRENT = 2          # ek waqt ma kitne rows judge ho rahe hon (1 = sab se stable)

# retriever config -- improvement rounds ma yahi badlega
FETCH_K = 10                # bi-encoder kitne laaye
TOP_K = 5                   # rerank ke baad kitne bachen

# ---------------------------------------------------------
# ek dafa banao (vector store + reranker load hona mehnga ha)
# ---------------------------------------------------------
retriever = RerankingRetriever(fetch_k=FETCH_K, top_k=TOP_K)
judge_llm = get_judge_llm()

context_recall = ContextRecall(llm=judge_llm)    # judge constructor ma diya
context_precision = ContextPrecision(llm=judge_llm)    # judge constructor ma diya

_slots = asyncio.Semaphore(MAX_CONCURRENT)


@experiment()    # is function ko RAGAS experiment bana do (.arun milega)
async def retriever_experiment(row):
    async with _slots:
        # 1. RETRIEVE (sync function ha, thread ma chalao taake event loop block na ho)
        docs = await asyncio.to_thread(retriever.invoke, row["query"])
        contexts = [d.page_content for d in docs]

        # 2. SCORE -- dono metrics same 3 cheezein dekhte hain
        recall, recall_reason = await safe_score(
            context_recall,
            user_input=row["query"],    # sawal (user_input)
            retrieved_contexts=contexts,    # retrieved chunks (list of strings)
            reference=row["ideal_answer"],    # golden / ideal jawab
        )
        precision, precision_reason = await safe_score(
            context_precision,
            user_input=row["query"],    # sawal (user_input)
            retrieved_contexts=contexts,    # retrieved chunks (list of strings)
            reference=row["ideal_answer"],    # golden / ideal jawab
        )

    return {
        **row,
        "retrieved_sessions": ", ".join(str(d.metadata.get("session", "?")) for d in docs),
        "context_recall": recall,
        "context_precision": precision,
        "recall_reason": recall_reason,
        "precision_reason": precision_reason,
        # config bhi saath log -- baad ma runs compare karne ke liye
        "fetch_k": FETCH_K,
        "top_k": TOP_K,
        **judge_info(),
    }


async def main():
    goldens = load_goldens(GOLDEN_PATH)
    print(f"Loaded {len(goldens)} golden cases from {GOLDEN_PATH}")

    rows = [
        {"id": g["id"], "query": g["query"], "ideal_answer": g["ideal_answer"]}
        for g in goldens
    ]
    dataset = build_dataset("retriever_goldens", rows)

    run_name = f"retriever_{datetime.now():%Y%m%d-%H%M%S}"
    results = await retriever_experiment.arun(dataset, name=run_name)    # har row pe chalao -> experiments/<run_name>.csv

    df = results.to_pandas()    # Experiment -> pandas DataFrame
    print_summary("retriever (component level)", df,
                  ["context_recall", "context_precision"], THRESHOLD)
    print(f"\nPoori detail (reasons ke saath): experiments/{run_name}.csv")


if __name__ == "__main__":
    asyncio.run(main())
