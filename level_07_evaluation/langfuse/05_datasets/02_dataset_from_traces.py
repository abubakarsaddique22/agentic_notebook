"""
Production traces se dataset — industry ka asli workflow.

Flow:
  1. Root observations query karo (naam, time range, error level wagera se filter)
  2. Unke input/output ko dataset items bana do — source_trace_id ke saath (UI mein trace ka link)
  3. UI mein review karke expected_output ko "gold" answer bana do

Pehle 04_production_tracing/02_sessions_and_users.py chala lo taake "chat-turn" traces mojood hon.
"""
from datetime import datetime, timedelta, timezone
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from langfuse import get_client  # noqa: E402

DATASET_NAME = "watch-support-from-traces"

if __name__ == "__main__":
    langfuse = get_client()

    # Observations API (v2): sirf root observations = har trace ka top-level step
    response = langfuse.api.observations.get_many(
        name="chat-turn",
        is_root_observation=True,
        from_start_time=datetime.now(timezone.utc) - timedelta(days=7),
        fields="core,basic,io",  # io = input/output bhi chahiye
        limit=20,
    )
    observations = response.data
    print(f"{len(observations)} 'chat-turn' observations mile.")
    if not observations:
        raise SystemExit("Pehle 04_production_tracing/02_sessions_and_users.py chalao (aur 1-2 minute ruko).")

    try:
        langfuse.get_dataset(DATASET_NAME)
    except Exception:
        langfuse.create_dataset(name=DATASET_NAME, description="Curated from production traces")

    for obs in observations:
        langfuse.create_dataset_item(
            dataset_name=DATASET_NAME,
            input=obs.input,
            expected_output=obs.output,  # abhi model ka jawab — UI mein review karke theek karna
            metadata={"source": "production", "session_id": obs.session_id or ""},
            source_trace_id=obs.trace_id,
            source_observation_id=obs.id,
        )
    print(f"{len(observations)} items '{DATASET_NAME}' mein add ho gaye.")
    print("UI: Datasets -> item kholo -> 'source trace' link se asal trace par ja sakte ho.")
