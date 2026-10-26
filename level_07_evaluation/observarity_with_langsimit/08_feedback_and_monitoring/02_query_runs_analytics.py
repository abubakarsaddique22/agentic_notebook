"""
Code se monitoring — runs query karke apni report banana.
(Daily Slack/email report, custom dashboards, alerts ke liye useful.)
"""
import os
import statistics
from datetime import datetime, timedelta, timezone
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from langsmith import Client  # noqa: E402
# ---------------------------------------------------------
# Client  (class) -- LangSmith API se baat karne wala object
#   Client() .env se LANGSMITH_API_KEY / LANGSMITH_ENDPOINT khud uthata ha.
#   Constructor options: api_key, api_url, hide_inputs / hide_outputs (masking
#   function ya True), anonymizer, auto_batch_tracing (default True).
#   Is project ma use hone wale methods:
#     list_projects()                         -> projects ki list
#     list_runs(project_name, is_root, error, start_time, filter, limit) -> traces query
#     has_dataset / read_dataset / create_dataset(dataset_name, description)
#     create_examples(dataset_id, examples=[{inputs, outputs, metadata, split}])
#     list_examples(dataset_name, splits=[...], as_of="prod")  -> examples parho
#     update_dataset_tag(dataset_name, as_of=datetime, tag)   -> version ko tag
#     evaluate(target, data, evaluators, summary_evaluators, experiment_prefix,
#              metadata, max_concurrency)                     -> experiment chalao
#     push_prompt(name, object=prompt) / pull_prompt("name:tag") -> Prompt Hub
#     create_feedback(run_id, key, score, comment, correction) -> user 👍/👎
#     create_presigned_feedback_token(run_id, feedback_key)   -> bina key wala URL
#     flush()                                 -> pending traces ABHI bhej do
# ---------------------------------------------------------

PROJECT = os.getenv("LANGSMITH_PROJECT", "langsmith-learning")


def percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    values = sorted(values)
    k = min(len(values) - 1, int(round(p / 100 * (len(values) - 1))))
    return values[k]


if __name__ == "__main__":
    client = Client()
    since = datetime.now(timezone.utc) - timedelta(days=1)

    # 1) Last 24h ke root traces
    runs = list(client.list_runs(project_name=PROJECT, is_root=True, start_time=since, limit=500))
    if not runs:
        raise SystemExit("Last 24h mein koi trace nahi. Pehle kuch scripts chalao.")

    errors = [r for r in runs if r.error]
    latencies = [(r.end_time - r.start_time).total_seconds() for r in runs if r.end_time]
    tokens = sum(r.total_tokens or 0 for r in runs)
    cost = sum(float(r.total_cost or 0) for r in runs)

    print(f"===== Report: {PROJECT} (last 24h) =====")
    print(f"Traces       : {len(runs)}")
    print(f"Error rate   : {len(errors) / len(runs):.1%}")
    print(f"Latency p50  : {statistics.median(latencies):.2f}s" if latencies else "Latency: n/a")
    print(f"Latency p95  : {percentile(latencies, 95):.2f}s")
    print(f"Total tokens : {tokens}")
    print(f"Total cost   : ${cost:.4f}")

    # 2) Sabse slow traces
    print("\nTop 3 slowest:")
    slow = sorted((r for r in runs if r.end_time), key=lambda r: r.end_time - r.start_time, reverse=True)
    for r in slow[:3]:
        print(f"  {r.name:<30} {(r.end_time - r.start_time).total_seconds():.2f}s  id={r.id}")

    # 3) Errors ki list
    print("\nErrors:")
    for r in errors[:5]:
        print(f"  {r.name}: {str(r.error)[:80]}")

    # 4) Negative feedback wale runs (filter query language)
    bad = list(
        client.list_runs(
            project_name=PROJECT,
            filter='and(eq(feedback_key, "user_rating"), eq(feedback_score, 0))',
            limit=10,
        )
    )
    print(f"\nNegative feedback runs: {len(bad)}")
    for r in bad:
        print(f"  {r.name}  inputs={str(r.inputs)[:60]}")
