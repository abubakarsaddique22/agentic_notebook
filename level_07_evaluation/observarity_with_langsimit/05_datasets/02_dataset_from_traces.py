"""
Production traces se dataset banana — industry ka asli workflow.

Flow:
  1. Project ke root runs query karo (filters: successful, kisi naam ke, last N din)
  2. Unke inputs/outputs ko dataset examples bana do
  3. Baad mein UI mein review karke galat outputs ko theek karo (reference answer)

Pehle 04_production_tracing/02_threads_conversations.py chala lo taake "Chat Turn" traces mojood hon.
"""
import os
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

SOURCE_PROJECT = os.getenv("LANGSMITH_PROJECT", "langsmith-learning")
DATASET_NAME = "watch-support-from-traces"


if __name__ == "__main__":
    client = Client()

    runs = list(
        client.list_runs(
            project_name=SOURCE_PROJECT,
            is_root=True,  # sirf top-level traces
            error=False,  # sirf successful
            start_time=datetime.now(timezone.utc) - timedelta(days=7),
            filter='eq(name, "Chat Turn")',  # LangSmith filter query language
            limit=20,
        )
    )
    print(f"{len(runs)} runs mile project '{SOURCE_PROJECT}' mein.")
    if not runs:
        raise SystemExit("Pehle 04_production_tracing/02_threads_conversations.py chalao.")

    if client.has_dataset(dataset_name=DATASET_NAME):
        dataset = client.read_dataset(dataset_name=DATASET_NAME)
    else:
        dataset = client.create_dataset(dataset_name=DATASET_NAME, description="Curated from prod traces")

    examples = [
        {
            "inputs": run.inputs,
            "outputs": run.outputs,
            "metadata": {"source_run_id": str(run.id), "source": "production"},
        }
        for run in runs
    ]
    client.create_examples(dataset_id=dataset.id, examples=examples)
    print(f"{len(examples)} examples '{DATASET_NAME}' mein add ho gaye.")
    print("Ab UI mein jao, examples review karo, aur galat outputs edit karke 'gold' answer bana do.")
