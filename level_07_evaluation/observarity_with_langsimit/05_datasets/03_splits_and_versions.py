"""
Splits aur Versions.

Splits:   dataset ke andar groups -> sirf "edge-cases" par eval chalana
Versions: har change (add/edit/delete example) dataset ka naya version banata hai.
          Kisi version ko tag karo (e.g. "prod") taake evals hamesha same fixed data par chalein
          — warna kal kisi ne example change kiya aur scores compare karne ke layak nahi rahe.
"""
from datetime import datetime, timezone
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

DATASET_NAME = "watch-support-qa"

if __name__ == "__main__":
    client = Client()

    # 1) Split filter
    edge = list(client.list_examples(dataset_name=DATASET_NAME, splits=["edge-cases"]))
    print(f"edge-cases split: {len(edge)} examples")
    for ex in edge:
        print("  -", ex.inputs["question"])

    # 2) Current version ko "prod" tag karo
    client.update_dataset_tag(
        dataset_name=DATASET_NAME,
        as_of=datetime.now(timezone.utc),
        tag="prod",
    )
    print("\nCurrent version ko 'prod' tag kar diya.")

    # 3) Tagged version read karo (evals mein yahi pass karte hain: data=client.list_examples(..., as_of="prod"))
    prod_examples = list(client.list_examples(dataset_name=DATASET_NAME, as_of="prod"))
    print(f"'prod' version mein {len(prod_examples)} examples.")
    print("\nUI: Dataset -> Examples tab -> top par version dropdown mein 'prod' tag dekho.")
