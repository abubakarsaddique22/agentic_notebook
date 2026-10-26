"""
Code se monitoring — apni report (daily Slack/email, custom dashboard, alerts).

  - Observations API: root observations (traces) -> error rate, latency, slowest
  - Metrics API: aggregated cost / tokens / count (group by model, name, ...)
  - Scores API: negative feedback wale traces
"""
import json
import statistics
from datetime import datetime, timedelta, timezone
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from langfuse import get_client  # noqa: E402

langfuse = get_client()
NOW = datetime.now(timezone.utc)
SINCE = NOW - timedelta(days=1)


def percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    values = sorted(values)
    return values[min(len(values) - 1, int(round(p / 100 * (len(values) - 1))))]


def traces_report() -> None:
    resp = langfuse.api.observations.get_many(
        is_root_observation=True, from_start_time=SINCE, fields="core,basic", limit=500
    )
    roots = resp.data
    if not roots:
        print("Last 24h mein koi trace nahi. Pehle kuch scripts chalao.")
        return

    errors = [o for o in roots if str(o.level).upper().endswith("ERROR")]
    latencies = [o.latency for o in roots if o.latency is not None]

    print("===== Traces (last 24h) =====")
    print(f"Traces      : {len(roots)}")
    print(f"Error rate  : {len(errors) / len(roots):.1%}")
    if latencies:
        print(f"Latency p50 : {statistics.median(latencies):.2f}")
        print(f"Latency p95 : {percentile(latencies, 95):.2f}")

    print("\nTop 3 slowest:")
    for o in sorted((o for o in roots if o.latency is not None), key=lambda o: o.latency, reverse=True)[:3]:
        print(f"  {o.name:<35} {o.latency:.2f}  trace={o.trace_id}")


def cost_report() -> None:
    query = {
        "view": "observations",
        "metrics": [
            {"measure": "count", "aggregation": "count"},
            {"measure": "totalTokens", "aggregation": "sum"},
            {"measure": "totalCost", "aggregation": "sum"},
        ],
        "dimensions": [{"field": "providedModelName"}],
        "filters": [],
        "fromTimestamp": SINCE.isoformat(),
        "toTimestamp": NOW.isoformat(),
    }
    result = langfuse.api.metrics.metrics(query=json.dumps(query))
    print("\n===== Cost by model (last 24h) =====")
    for row in result.data:
        print(" ", row)


def negative_feedback() -> None:
    resp = langfuse.api.scores.get_many(name="user_rating", value="0", from_timestamp=SINCE, limit=20)
    print(f"\n===== Negative feedback: {len(resp.data)} =====")
    for s in resp.data:
        subject_id = getattr(s.subject, "id", None)
        print(f"  {s.name}={s.value}  comment={s.comment!r}  on={subject_id}")


if __name__ == "__main__":
    traces_report()
    cost_report()
    negative_feedback()
