"""
APPLICATION LEVEL -- CITATION behaviour (RAGAS + programmatic)
==============================================================

App ka citation mode (rag.invoke_with_citations): har claim ke baad [Session N] lagta ha.
Teen cheezein check karte hain:

    1. citation_present  (programmatic) -- answer ma koi citation ha?
                         (abstain kiya ho to citation nahi honi chahiye -> pass)
    2. citation_valid    (programmatic) -- jo sessions cite kiye, kya wo sach ma RETRIEVED
                         context ma the? Invented session number = fail.
                         score = valid cited sessions / total cited sessions
    3. citation_support  (RAGAS DiscreteMetric, LLM judge) -- jis claim pe [Session N] laga,
                         kya Session N wala chunk sach ma wo baat kehta ha?
                         (label sahi format ma ho kar bhi GALAT jagah laga ho sakta ha)

1-2 code se (deterministic, free, fast), 3 judge se (semantic) -- notes wala rule:
jo cheez code check kar sake, uske liye LLM mat lagao.

Run (project root se):
    python -m evals.03_application.eval_citation
"""

import asyncio
import re
import traceback
from datetime import datetime

from dotenv import load_dotenv

from src.rag_pipeline import RagPipeline

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

from judge import get_judge_llm, judge_info
from harness import build_dataset, load_goldens, print_summary, safe_score

load_dotenv()

GOLDEN_PATH = "goldens/retriever_goldens.json"
THRESHOLD = 0.7
MAX_CONCURRENT = 2
ABSTAIN_TEXT = "I don't have enough information in the course material"
CITE_RE = re.compile(r"\[Session\s*(\d+)\]")

rag = RagPipeline()
judge_llm = get_judge_llm()

citation_support = DiscreteMetric(
    name="citation_support",    # metric ka naam (CSV / result ma)
    allowed_values=["pass", "fail"],    # judge sirf inhi ma se ek value dega
    prompt="""You are auditing citations in an answer. Every context chunk below starts with its source label, e.g. [Session 3].
The answer puts labels like [Session 3] after its claims.

For EVERY claim that carries a citation label, check that a chunk with THAT SAME label actually supports the claim.
Ignore claims without a label. Do not judge writing quality.

Context chunks:
{contexts}

Answer:
{response}

Return "pass" if every cited claim is supported by a chunk with the cited label.
Return "fail" if any cited claim is not supported by the session it cites. In the reason, quote the wrong citation.""",
)

_slots = asyncio.Semaphore(MAX_CONCURRENT)


def programmatic_checks(answer: str, retrieved_sessions: list[str]) -> tuple[float, float, list[str]]:
    cited = CITE_RE.findall(answer)
    abstained = ABSTAIN_TEXT.lower() in answer.lower()

    if abstained:
        # abstain = koi citation nahi honi chahiye
        ok = 1.0 if not cited else 0.0
        return ok, ok, cited

    present = 1.0 if cited else 0.0
    if not cited:
        return present, 0.0, cited

    retrieved = set(retrieved_sessions)
    valid = sum(1 for s in cited if s in retrieved) / len(cited)
    return present, valid, cited


@experiment()    # is function ko RAGAS experiment bana do (.arun milega)
async def citation_experiment(row):
    try:
        return await _citation_row(row)
    except Exception as e:                      # row gum na ho -- error CSV ma aaye
        nan = float("nan")
        return {**row, "answer": "", "citation_present": nan, "citation_valid": nan,
                "citation_support": nan,
                "row_error": f"{type(e).__name__}: {e} | {traceback.format_exc(limit=-3)}"}


async def _citation_row(row):
    async with _slots:
        out = await asyncio.to_thread(rag.invoke_with_citations, row["query"])
        answer, sessions, contexts = out["answer"], out["sessions"], out["context"]

        present, valid, cited = programmatic_checks(answer, sessions)

        if cited:
            support, support_reason = await safe_score(
                citation_support,
                llm=judge_llm,    # DiscreteMetric ko llm har ascore call pe dena hota ha
                contexts="\n\n".join(contexts),   # already "[Session N] text" format ma
                response=answer,    # bot ka jawab -- yahi judge hota ha
            )
        else:
            support, support_reason = present, "no citations to audit"

    return {
        **row,
        "answer": answer,
        "retrieved_sessions": ", ".join(sessions),
        "cited_sessions": ", ".join(sorted(set(cited), key=int)),
        "citation_present": present,
        "citation_valid": valid,
        "citation_support": support,
        "support_reason": support_reason,
        "row_error": "",
        **judge_info(),
    }


async def main():
    goldens = load_goldens(GOLDEN_PATH)
    print(f"Loaded {len(goldens)} golden cases from {GOLDEN_PATH}")

    rows = [{"id": g["id"], "query": g["query"]} for g in goldens]
    dataset = build_dataset("citation_goldens", rows)

    run_name = f"citation_{datetime.now():%Y%m%d-%H%M%S}"
    results = await citation_experiment.arun(dataset, name=run_name)    # har row pe chalao -> experiments/<run_name>.csv

    df = results.to_pandas()    # Experiment -> pandas DataFrame
    print_summary("citation behaviour", df,
                  ["citation_present", "citation_valid", "citation_support"], THRESHOLD)
    print(f"\nPoori detail (answers + cited vs retrieved sessions): experiments/{run_name}.csv")


if __name__ == "__main__":
    asyncio.run(main())
