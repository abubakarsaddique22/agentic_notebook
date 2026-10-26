import asyncio
import json
import time
from collections import Counter
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
from ragas.metrics.collections import AnswerRelevancy, ContextRelevance, Faithfulness
# ---------------------------------------------------------
# ragas.metrics.collections  (RAGAS 0.4 ke naye "modern" metrics)
#   Sab ka pattern ek jaisa:
#     metric = SomeMetric(llm=judge_llm, ...)          # judge CONSTRUCTOR ma
#     result = await metric.ascore(field1=..., ...)     # sirf zaroori fields
#     result.value  -> score (aksar 0.0 se 1.0, zyada = behtar)
#     result.reason -> wajah (har metric nahi deta)
#   harness.safe_score() yahi ascore() chalata ha aur error pe NaN deta ha.
#
# ContextRelevance(llm, max_retries=5)  -- retrieved context kitna kaam ka
#   ascore(user_input, retrieved_contexts)   (reference nahi chahiye)
#   Kaise: DO judge prompts (NVIDIA dual-judge) har ek 0 / 1 / 2 rating deta ha
#          (relevant nahi / thora / poora). Dono ka average -> 0.0-1.0.
#   Low = retriever galat ya noisy chunks laa raha ha
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
#
# RAG TRIAD: ContextRelevance (retriever) + Faithfulness + AnswerRelevancy
# (generator). Teeno REFERENCE-FREE -- golden answer nahi chahiye.
# ---------------------------------------------------------

from judge import get_judge_embeddings, get_judge_llm, judge_info
from harness import build_dataset, load_goldens, print_latency, print_summary, safe_score

load_dotenv()

GOLDEN_PATH = "goldens/retriever_goldens.json"   # sirf "query" chahiye (triad reference-free ha)
THRESHOLD = 0.7
MAX_CONCURRENT = 2

FETCH_K = 10
TOP_K = 5

# ---------------------------------------------------------
# ek dafa banao
# ---------------------------------------------------------
rag = RagPipeline(fetch_k=FETCH_K, top_k=TOP_K)
judge_llm = get_judge_llm()
judge_embeddings = get_judge_embeddings()

context_relevance = ContextRelevance(llm=judge_llm)    # dual judge 0/1/2 -> 0..1
faithfulness = Faithfulness(llm=judge_llm)    # claims vs context -- sirf LLM chahiye
answer_relevancy = AnswerRelevancy(llm=judge_llm, embeddings=judge_embeddings)    # LLM (ulte sawal) + embeddings (cosine)

_slots = asyncio.Semaphore(MAX_CONCURRENT)


def diagnose(cr: float, faith: float, ar: float) -> str:
    """Triad scores se root cause nikalo (NaN = judge error)."""
    scores = (cr, faith, ar)
    if any(s != s for s in scores):              # NaN check
        return "judge_error"
    if cr < THRESHOLD:
        return "retrieval"                       # galat / noisy context aaya
    if faith < THRESHOLD:
        return "generation_unfaithful"           # context theek, answer us se bahar
    if ar < THRESHOLD:
        return "generation_off_question"         # grounded, lekin sawal ka jawab nahi
    return "ok"


@experiment()    # is function ko RAGAS experiment bana do (.arun milega)
async def pipeline_experiment(row):
    async with _slots:
        # 1. POORA PIPELINE chalao (retrieve + rerank + generate) aur time lo
        t0 = time.perf_counter()
        out = await asyncio.to_thread(rag.invoke, row["query"])
        latency = time.perf_counter() - t0

        query, contexts, answer = out["query"], out["context"], out["answer"]

        # 2. RAG TRIAD
        cr, cr_reason = await safe_score(
            context_relevance,
            user_input=query,    # sawal (user_input)
            retrieved_contexts=contexts,    # retrieved chunks (list of strings)
        )
        faith, faith_reason = await safe_score(
            faithfulness,
            user_input=query,    # sawal (user_input)
            response=answer,    # bot ka jawab -- yahi judge hota ha
            retrieved_contexts=contexts,    # retrieved chunks (list of strings)
        )
        ar, ar_reason = await safe_score(
            answer_relevancy,
            user_input=query,    # sawal (user_input)
            response=answer,    # bot ka jawab -- yahi judge hota ha
        )

    return {
        **row,
        "answer": answer,
        "contexts": json.dumps(contexts, ensure_ascii=False),
        "context_relevance": cr,
        "faithfulness": faith,
        "answer_relevancy": ar,
        "root_cause": diagnose(cr, faith, ar),
        "latency_s": round(latency, 2),
        "context_relevance_reason": cr_reason,
        "faithfulness_reason": faith_reason,
        "relevancy_reason": ar_reason,
        "fetch_k": FETCH_K,
        "top_k": TOP_K,
        "generator_model": GENERATOR_MODEL,
        **judge_info(),
    }


async def main():
    goldens = load_goldens(GOLDEN_PATH)
    print(f"Loaded {len(goldens)} golden cases from {GOLDEN_PATH}")

    rows = [{"id": g["id"], "query": g["query"]} for g in goldens]
    dataset = build_dataset("pipeline_goldens", rows)

    run_name = f"pipeline_{datetime.now():%Y%m%d-%H%M%S}"
    results = await pipeline_experiment.arun(dataset, name=run_name)    # har row pe chalao -> experiments/<run_name>.csv

    df = results.to_pandas()    # Experiment -> pandas DataFrame
    print_summary("rag pipeline (rag triad)", df,
                  ["context_relevance", "faithfulness", "answer_relevancy"], THRESHOLD)

    print("\nROOT CAUSE (failure kahan ha):")
    for cause, n in Counter(df["root_cause"]).most_common():
        print(f"  {cause:<26} {n}")

    print_latency(df)
    print(f"\nPoori detail (answers, contexts, reasons): experiments/{run_name}.csv")


if __name__ == "__main__":
    asyncio.run(main())
