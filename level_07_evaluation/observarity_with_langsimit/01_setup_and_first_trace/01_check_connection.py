"""
Step 1: Check karo ke setup sahi hai.

Yeh script:
  - .env load karti hai
  - zaroori env vars check karti hai
  - LangSmith API se connect hokar tumhare projects list karti hai
"""
import os
from pathlib import Path

from dotenv import load_dotenv

# .env hamesha root folder se load hogi (langsmith import se PEHLE load karna zaroori hai)
ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

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


def check_env() -> bool:
    required = ["LANGSMITH_API_KEY", "LANGSMITH_TRACING", "GROQ_API_KEY"]
    ok = True
    for key in required:
        value = os.getenv(key)
        if not value or "xxxx" in value:
            print(f"[MISSING] {key}  -> .env file mein set karo")
            ok = False
        else:
            print(f"[OK]      {key} = {value[:8]}...")
    print(f"[INFO]    LANGSMITH_PROJECT = {os.getenv('LANGSMITH_PROJECT', 'default')}")
    return ok


def check_langsmith_connection() -> None:
    client = Client()
    projects = list(client.list_projects(limit=5))
    print(f"\n[OK] LangSmith se connect ho gaya. Tumhare {len(projects)} project(s):")
    for p in projects:
        print(f"   - {p.name}")


if __name__ == "__main__":
    if check_env():
        check_langsmith_connection()
        print("\nSetup complete. Ab 02_first_trace.py chalao.")
    else:
        print("\nPehle .env theek karo.")
