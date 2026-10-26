"""
M7.6 -- CUSTOM MODEL EVAL: apne TASK ke liye model chunna (RAGAS + programmatic)
================================================================================

Leaderboard batata ha kaunsa model "general" ma acha ha. Lekin sawal ye ha: MERE kaam
pe kaunsa model kaafi acha + sab se tez/sasta ha? Iska jawab sirf apni eval deti ha.

Task: Text-to-SQL -- store owner urdu/english ma sawal poochta ha, model SQLite query
likhta ha (goldens/text_to_sql_goldens.json, 15 sawal: easy / medium / hard).

Workflow (roadmap M7.6):
    1. Shortlist     -- leaderboard / model page se 2-4 candidates (yahan --models)
    2. Same setup    -- har model ko SAME schema, SAME prompt, SAME sawal, temperature 0
    3. Score         -- neeche wale metrics
    4. Trade-off     -- quality vs latency vs tokens/cost -> sab se "acha kaafi" + sasta

Metrics (har model x har sawal):
    exact_match           (code)  SQL string reference jaisi? -- jaan-boojh kar rakha ha taake
                                  dikhe ke ye BEKAAR metric ha: ek result kai queries se aata ha
    valid_sql             (code)  query chali (syntax error / ghalat column nahi)?
    execution_accuracy    (code)  dono queries DATABASE pe chalao, RESULT TABLES compare karo
                                  (notes wala sahi tareeqa -- main metric)
    data_compare_f1       (RAGAS DataCompyScore) result tables ki row-level F1 (partial credit)
    sql_equivalent        (RAGAS SQLSemanticEquivalence, LLM judge) judge ke hisaab se dono
                                  queries ka matlab same ha?
    latency_s, tokens     (captured)

Run (project root se):
    ollama pull gpt-oss:120b-cloud                 # jo bhi models compare karne hain
    python -m evals.09_model_selection.eval_model_selection
    python -m evals.09_model_selection.eval_model_selection --models gpt-oss:20b-cloud qwen2.5-coder:1.5b

Optional cost (.env):  PRICES_PER_1M=gpt-oss:20b-cloud=0.05/0.20,gpt-oss:120b-cloud=0.10/0.50
                       (input/output $ per 1M tokens -- apni provider ki rates daalo)
"""

import argparse
import asyncio
import io
import json
import math
import os
import re
import threading
import time
from datetime import datetime

import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI

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
from ragas.metrics.collections import DataCompyScore, SQLSemanticEquivalence
# ---------------------------------------------------------
# ragas.metrics.collections  (RAGAS 0.4 ke naye "modern" metrics)
#   Sab ka pattern ek jaisa:
#     metric = SomeMetric(llm=judge_llm, ...)          # judge CONSTRUCTOR ma
#     result = await metric.ascore(field1=..., ...)     # sirf zaroori fields
#     result.value  -> score (aksar 0.0 se 1.0, zyada = behtar)
#     result.reason -> wajah (har metric nahi deta)
#   harness.safe_score() yahi ascore() chalata ha aur error pe NaN deta ha.
#
# DataCompyScore(mode="rows", metric="f1")  -- do TABLES compare (LLM nahi)
#   ascore(reference, response)   -- dono CSV STRING honi chahiye
#   datacompy library se table compare karta ha:
#     mode   -> "rows" (row-level match) ya "columns" (column-level)
#     metric -> "precision" (predicted rows ma se kitni sahi) /
#               "recall" (reference rows ma se kitni mili) / "f1" (dono)
#   Faida: partial credit -- 10 ma se 9 rows sahi hon to 0 nahi milta.
#
# SQLSemanticEquivalence(llm)  -- do SQL queries ka MATLAB same ha? (LLM judge)
#   ascore(response, reference, reference_contexts=None)
#     response           -> model ki SQL
#     reference          -> golden SQL
#     reference_contexts -> (optional) DB schema list -- judge ko tables/columns dikhein
#   Score: 1.0 = same result denge, 0.0 = nahi. Syntax alag ho sakta ha.
#   Note: ye judge ki RAI ha -- asal sach execution_accuracy (code) ha.
#
# DataCompyScore ke liye `datacompy<1.0` install hona chahiye (requirements.txt).
# ---------------------------------------------------------

from judge import OLLAMA_API_KEY, OLLAMA_BASE_URL, get_judge_llm, judge_info
from harness import build_dataset, load_goldens, safe_score

from .store_db import SCHEMA, build_db

load_dotenv()

GOLDEN_PATH = "goldens/text_to_sql_goldens.json"
DEFAULT_MODELS = os.getenv("SQL_MODELS", "gpt-oss:20b-cloud,gpt-oss:120b-cloud").split(",")
MAX_CONCURRENT = 2
ACC_TOLERANCE = 0.05     # best model se 5% tak kam accuracy = "acha kaafi"

SYSTEM_PROMPT = f"""You are an expert SQLite analyst for an online watch store in Pakistan.
Write ONE SQLite SELECT query that answers the user's question using this schema:

{SCHEMA}

Rules: return only the SQL inside a ```sql code block. Read-only: SELECT / WITH only."""

db = build_db()
_db_lock = threading.Lock()
client = OpenAI(base_url=OLLAMA_BASE_URL, api_key=OLLAMA_API_KEY, timeout=300)

judge_llm = get_judge_llm()
data_compare = DataCompyScore(mode="rows", metric="f1")    # row-level F1, LLM nahi
sql_equivalence = SQLSemanticEquivalence(llm=judge_llm)    # LLM judge: dono SQL ka matlab same? 1/0
_slots = asyncio.Semaphore(MAX_CONCURRENT)


def parse_prices() -> dict:
    out = {}
    for part in filter(None, os.getenv("PRICES_PER_1M", "").split(",")):
        model, _, rates = part.partition("=")
        p_in, _, p_out = rates.partition("/")
        out[model.strip()] = (float(p_in), float(p_out))
    return out


PRICES = parse_prices()


# ---------------------------------------------------------
# model call + SQL helpers
# ---------------------------------------------------------
def ask_model(model: str, question: str) -> dict:
    kwargs = {"reasoning_effort": "low"} if "gpt-oss" in model else {}
    t0 = time.perf_counter()
    resp = client.chat.completions.create(
        model=model, temperature=0,
        messages=[{"role": "system", "content": SYSTEM_PROMPT},
                  {"role": "user", "content": question}],
        **kwargs,
    )
    usage = resp.usage
    return {
        "raw": resp.choices[0].message.content or "",
        "latency_s": time.perf_counter() - t0,
        "input_tokens": getattr(usage, "prompt_tokens", 0) or 0,
        "output_tokens": getattr(usage, "completion_tokens", 0) or 0,
    }


def extract_sql(text: str) -> str:
    m = re.search(r"```(?:sql)?\s*(.*?)```", text, re.S | re.I)
    sql = (m.group(1) if m else text).strip()
    return sql.split(";")[0].strip() + ";" if sql else ""


def run_sql(sql: str):
    """(rows, columns, error). Sirf read-only queries -- model ki query DB na badal sake."""
    if not re.match(r"^\s*(select|with)\b", sql, re.I):
        return None, None, "not a SELECT/WITH query"
    try:
        with _db_lock:
            cur = db.execute(sql)
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description or []]
        return rows, cols, ""
    except Exception as e:
        return None, None, f"{type(e).__name__}: {e}"


def _norm_value(v):
    if isinstance(v, float):
        return f"{round(v, 2):g}"
    return str(v).strip().lower()


def same_result(pred_rows, ref_rows) -> bool:
    """Column ke naam / order aur row order ignore -- sirf DATA same ha?"""
    norm = lambda rows: sorted(tuple(sorted(_norm_value(v) for v in r)) for r in rows)
    return norm(pred_rows) == norm(ref_rows)


def to_csv(rows) -> str:
    """DataCompy ke liye: column naam c0..cN (alias ka farq ignore), rows sorted."""
    width = max((len(r) for r in rows), default=1)
    data = sorted([[_norm_value(v) for v in r] + [""] * (width - len(r)) for r in rows])
    buf = io.StringIO()
    pd.DataFrame(data, columns=[f"c{i}" for i in range(width)]).to_csv(buf, index=False)
    return buf.getvalue()


def _squash(sql: str) -> str:
    return re.sub(r"\s+", " ", sql.strip().rstrip(";").lower())


# ---------------------------------------------------------
# experiment: har row = (model, sawal)
# ---------------------------------------------------------
@experiment()    # is function ko RAGAS experiment bana do (.arun milega)
async def model_selection_experiment(row):
    ref_rows, _, ref_err = run_sql(row["reference_sql"])
    assert not ref_err, f"golden SQL toota hua ha: {row['id']} {ref_err}"

    async with _slots:
        try:
            out = await asyncio.to_thread(ask_model, row["model"], row["question"])
            call_error = ""
        except Exception as e:
            out = {"raw": "", "latency_s": float("nan"), "input_tokens": 0, "output_tokens": 0}
            call_error = f"{type(e).__name__}: {e}"

        sql = extract_sql(out["raw"])
        pred_rows, _, sql_error = run_sql(sql) if sql else (None, None, "no SQL in reply")
        valid = pred_rows is not None

        exec_acc = float(valid and same_result(pred_rows, ref_rows))
        if valid:
            dc, _ = await safe_score(data_compare, reference=to_csv(ref_rows), response=to_csv(pred_rows))
            dc = 0.0 if math.isnan(dc) else dc
        else:
            dc = 0.0
        if sql:
            eq, eq_reason = await safe_score(sql_equivalence, response=sql,
                                             reference=row["reference_sql"], reference_contexts=[SCHEMA])
        else:
            eq, eq_reason = 0.0, "no SQL"

    p_in, p_out = PRICES.get(row["model"], (0.0, 0.0))
    return {
        **row,
        "predicted_sql": sql,
        "exact_match": float(_squash(sql) == _squash(row["reference_sql"])),
        "valid_sql": float(valid),
        "execution_accuracy": exec_acc,
        "data_compare_f1": dc,
        "sql_equivalent": eq,
        "latency_s": round(out["latency_s"], 2),
        "input_tokens": out["input_tokens"],
        "output_tokens": out["output_tokens"],
        "cost_usd": out["input_tokens"] / 1e6 * p_in + out["output_tokens"] / 1e6 * p_out,
        "error": call_error or sql_error,
        "equivalence_reason": eq_reason,
        **judge_info(),
    }


# ---------------------------------------------------------
# report + decision
# ---------------------------------------------------------
def pct(values, p):
    values = sorted(v for v in values if not math.isnan(v))
    return values[min(len(values) - 1, int(round(p / 100 * (len(values) - 1))))] if values else float("nan")


def report(df: pd.DataFrame):
    quality = ["exact_match", "valid_sql", "execution_accuracy", "data_compare_f1", "sql_equivalent"]
    stats = []
    for model, part in df.groupby("model"):
        lat = part["latency_s"].astype(float).tolist()
        s = {"model": model, "n": len(part)}
        for q in quality:
            s[q] = pd.to_numeric(part[q], errors="coerce").mean()
        s["p50_latency_s"] = pct(lat, 50)
        s["p95_latency_s"] = pct(lat, 95)
        s["avg_tokens"] = (part["input_tokens"].astype(float) + part["output_tokens"].astype(float)).mean()
        s["cost_per_1k_usd"] = part["cost_usd"].astype(float).mean() * 1000
        stats.append(s)
    st = pd.DataFrame(stats).set_index("model")

    pd.set_option("display.width", 200)
    print("\n" + "=" * 100)
    print("MODEL COMPARISON (same prompt, same schema, same 15 questions, temperature 0)")
    print("=" * 100)
    print(st.round(3).to_string())

    print("\nEXECUTION ACCURACY BY DIFFICULTY:")
    print(df.pivot_table(index="model", columns="difficulty", values="execution_accuracy",
                         aggfunc="mean").round(2).to_string())

    print("\nExact match vs execution accuracy -- dekho kitni SAHI queries string-match fail karti hain:")
    for model, part in df.groupby("model"):
        hidden = int(((part["execution_accuracy"] == 1) & (part["exact_match"] == 0)).sum())
        print(f"  {model}: {hidden} queries sahi result deti hain lekin string reference se alag ha")

    # decision: best accuracy ke 5% andar wale models ma se sab se sasta / tez
    best = st["execution_accuracy"].max()
    good_enough = st[st["execution_accuracy"] >= best - ACC_TOLERANCE]
    key = "cost_per_1k_usd" if PRICES else "p50_latency_s"
    chosen = good_enough.sort_values([key, "avg_tokens"]).index[0]
    print("\nDECISION:")
    print(f"  best execution accuracy = {best:.0%}; 'acha kaafi' = {best - ACC_TOLERANCE:.0%}+ -> {list(good_enough.index)}")
    print(f"  in ma se sab se {'sasta' if PRICES else 'tez'} ({key}) -> CHOSEN: {chosen}")
    return st, chosen


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="+", default=DEFAULT_MODELS)
    args = ap.parse_args()

    goldens = load_goldens(GOLDEN_PATH)
    print(f"Loaded {len(goldens)} questions; models: {args.models}")

    rows = [{"id": f"{m}|{g['id']}", "model": m, "question": g["question"],
             "difficulty": g["difficulty"], "reference_sql": g["reference_sql"]}
            for m in args.models for g in goldens]
    dataset = build_dataset("model_selection", rows)

    run_name = f"model_selection_{datetime.now():%Y%m%d-%H%M%S}"
    results = await model_selection_experiment.arun(dataset, name=run_name)    # har row pe chalao -> experiments/<run_name>.csv
    df = results.to_pandas()    # Experiment -> pandas DataFrame

    errors = df[df["error"].fillna("").astype(str) != ""]
    if len(errors):
        print(f"\n{len(errors)} rows ma error (pehli 3):")
        for _, r in errors.head(3).iterrows():
            print(f"  [{r['id']}] {str(r['error'])[:200]}")

    st, chosen = report(df)
    os.makedirs("regression", exist_ok=True)
    with open(f"regression/{run_name}.json", "w", encoding="utf-8") as f:
        json.dump({"chosen": chosen, "stats": st.reset_index().to_dict(orient="records")}, f, indent=2)
    print(f"\nPoori detail (har query + predicted SQL): experiments/{run_name}.csv")


if __name__ == "__main__":
    asyncio.run(main())
