"""
harness.py -- har eval file ke common helpers (sirf RAGAS + Python).

    load_goldens(path)            -> golden JSON ki list
    build_dataset(name, rows)     -> ragas Dataset (local/csv, datasets/<name>.csv ma save)
    safe_score(metric, **kwargs)  -> (value, reason) -- ek metric fail ho to poora run na ruke
                                     ("pass"/"fail" wale DiscreteMetric -> 1.0 / 0.0)
    print_summary(title, df, ...) -> har metric ka average + pass/fail
    print_latency(df)             -> p50 / p95 / max latency (operational metric)
"""

import json
import math

from ragas import Dataset
# ---------------------------------------------------------
# Dataset  (RAGAS ka data table -- golden rows rakhne ke liye)
#   Dataset(name, backend, root_dir):
#     name     -> dataset ka naam (file ka naam bhi yahi)
#     backend  -> kahan save ho: "local/csv" = root_dir/datasets/<name>.csv
#                 ("local/jsonl" bhi hota ha)
#     root_dir -> project folder (yahan "."); experiments bhi isi ke andar
#                 experiments/ folder ma save hote hain
#   Methods:
#     .append(row_dict) -> ek row add
#     .save()           -> file ma likho
#     .load(name, backend, ...) -> (classmethod) purana dataset wapas parho
#     .to_pandas()      -> DataFrame
#     len(ds), for row in ds -> rows gino / ek ek row lo
#   CSV ma list ya dict seedhi nahi jaati -> pehle json.dumps, baad ma json.loads.
#   experiment.arun(dataset) isi ki har row experiment function ko deta ha.
# ---------------------------------------------------------


def load_goldens(path: str) -> list[dict]:
    with open(path, encoding="utf-8-sig") as f:      # -sig: Windows BOM ho to bhi chal jaye
        return json.load(f)


def build_dataset(name: str, rows: list[dict]) -> Dataset:
    """
    Golden rows ko RAGAS Dataset bana kar datasets/<name>.csv ma save karta ha.
    CSV ma list (jaise contexts) seedhi nahi ja sakti, isliye list wale fields
    caller pehle json.dumps kar ke deta ha.
    """
    dataset = Dataset(name=name, backend="local/csv", root_dir=".")    # -> ./datasets/<name>.csv
    for row in rows:
        dataset.append(row)    # ek row add (dict)
    dataset.save()    # CSV file ma likh do
    return dataset


PASS_FAIL = {"pass": 1.0, "fail": 0.0}


def to_float(value) -> float:
    """Numeric score waise hi; DiscreteMetric ka 'pass'/'fail' -> 1.0 / 0.0."""
    if isinstance(value, str):
        return PASS_FAIL.get(value.strip().lower(), float("nan"))
    return float(value)


async def safe_score(metric, **kwargs):
    """metric.ascore(...) chalao; error aaye to NaN + error message return karo."""
    try:
        result = await metric.ascore(**kwargs)    # MetricResult: .value + .reason
        return to_float(result.value), (result.reason or "")
    except Exception as e:                       # judge ka JSON toot gaya, timeout, etc.
        return float("nan"), f"ERROR: {type(e).__name__}: {e}"


def print_row_errors(df):
    """Jin rows ma eval khud crash hua (judge nahi, poora row) unka error dikhao."""
    if "row_error" not in df.columns:
        return
    errs = [e for e in df["row_error"].tolist() if isinstance(e, str) and e]
    if errs:
        print(f"\nROW ERRORS ({len(errs)}/{len(df)} rows crash huay):")
        for e in sorted(set(errs)):
            print(f"  x {e[:600]}")


def print_summary(title: str, df, metric_cols: list[str], threshold: float):
    print("\n" + "=" * 60)
    print(f"{title.upper()}  ({len(df)} test cases, threshold {threshold})")
    print("=" * 60)

    if len(df) == 0:
        print("Koi row wapas nahi aayi -- upar 'Warning: Task failed with error' lines dekho.")
        return
    print_row_errors(df)
    metric_cols = [c for c in metric_cols if c in df.columns]

    for col in metric_cols:
        values = [float(v) for v in df[col].tolist()]
        ok = [v for v in values if not math.isnan(v)]
        errors = len(values) - len(ok)
        passed = sum(v >= threshold for v in ok)
        avg = sum(ok) / len(ok) if ok else float("nan")
        print(f"{col:<22} avg = {avg:6.1%}   pass {passed}/{len(values)}   errors {errors}")

    # sab se kam score wale cases -- yahi analyze karne hain
    print("\nFAILED cases (kisi bhi metric pe threshold se neeche ya error):")
    any_fail = False
    for _, row in df.iterrows():
        bad = [c for c in metric_cols if math.isnan(float(row[c])) or float(row[c]) < threshold]
        if bad:
            any_fail = True
            scores = ", ".join(f"{c}={float(row[c]):.2f}" for c in metric_cols)
            print(f"  [{row['id']}] {row['query'][:70]}")
            print(f"        {scores}")
    if not any_fail:
        print("  koi nahi")


def print_latency(df, col: str = "latency_s"):
    """Operational metric: average nahi, percentiles dekho (P95 = 'slow users' ka tajurba)."""
    values = sorted(float(v) for v in df[col].tolist())
    if not values:
        return

    def pct(p):
        return values[min(len(values) - 1, int(round(p / 100 * (len(values) - 1))))]

    print(f"\nLATENCY (per query, sirf RAG app ka time, judge ka nahi):")
    print(f"  p50 = {pct(50):.1f}s   p95 = {pct(95):.1f}s   max = {values[-1]:.1f}s")


def print_by_group(df, group_col: str, metric_cols: list[str]):
    """Group-wise pass rate (jaise attack vs benign) -- safety ma average se zyada zaroori."""
    print(f"\nBY {group_col.upper()}:")
    for group, part in df.groupby(group_col):
        cells = []
        for col in metric_cols:
            vals = [float(v) for v in part[col].tolist()]
            ok = [v for v in vals if not math.isnan(v)]
            rate = sum(ok) / len(ok) if ok else float("nan")
            cells.append(f"{col}={rate:5.0%}")
        print(f"  {str(group):<24} n={len(part):<3} " + "  ".join(cells))
