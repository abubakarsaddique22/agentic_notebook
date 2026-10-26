"""
Dataset banana — code se (version control mein rehta hai, team share kar sakti hai).

Idempotent: dobara chalao to duplicate nahi banega.
"""
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

EXAMPLES = [
    # ---- normal FAQs ----
    {
        "inputs": {"question": "Delivery kitne din mein hoti hai?"},
        "outputs": {"answer": "Lahore mein 1-2 din, baqi Pakistan mein 3-5 working days."},
        "metadata": {"category": "delivery"},
        "split": "test",
    },
    {
        "inputs": {"question": "Kya online payment ho sakti hai?"},
        "outputs": {"answer": "Nahi, abhi sirf Cash on Delivery (COD) available hai."},
        "metadata": {"category": "payment"},
        "split": "test",
    },
    {
        "inputs": {"question": "Return ya exchange policy kya hai?"},
        "outputs": {"answer": "Delivery ke 7 din ke andar exchange ho sakta hai agar product unused ho."},
        "metadata": {"category": "returns"},
        "split": "test",
    },
    {
        "inputs": {"question": "Delivery charges kitne hain?"},
        "outputs": {"answer": "Rs. 3000 se upar order par free delivery, warna Rs. 200."},
        "metadata": {"category": "delivery"},
        "split": "test",
    },
    {
        "inputs": {"question": "Kya watches par warranty hai?"},
        "outputs": {"answer": "Haan, machine par 6 mahine ki warranty hai."},
        "metadata": {"category": "warranty"},
        "split": "test",
    },
    # ---- edge cases (bot ko yahan fail nahi hona chahiye) ----
    {
        "inputs": {"question": "Mujhe bitcoin mein payment karni hai"},
        "outputs": {"answer": "Maazrat, sirf Cash on Delivery available hai."},
        "metadata": {"category": "payment"},
        "split": "edge-cases",
    },
    {
        "inputs": {"question": "Aaj cricket match kaun jeetega?"},
        "outputs": {"answer": "Main sirf store se related sawalon mein madad kar sakta hoon."},
        "metadata": {"category": "off-topic"},
        "split": "edge-cases",
    },
]


def get_or_create_dataset(client: Client):
    if client.has_dataset(dataset_name=DATASET_NAME):
        print(f"Dataset '{DATASET_NAME}' pehle se mojood hai.")
        return client.read_dataset(dataset_name=DATASET_NAME), False
    ds = client.create_dataset(
        dataset_name=DATASET_NAME,
        description="Watch store support bot ke golden Q&A (FAQ + edge cases)",
    )
    print(f"Dataset '{DATASET_NAME}' ban gaya.")
    return ds, True


if __name__ == "__main__":
    client = Client()
    dataset, created = get_or_create_dataset(client)
    if created:
        client.create_examples(dataset_id=dataset.id, examples=EXAMPLES)
        print(f"{len(EXAMPLES)} examples add ho gaye.")

    count = len(list(client.list_examples(dataset_id=dataset.id)))
    print(f"Total examples: {count}")
