"""
Golden dataset for the capstone bot.

Chalao (09_capstone_support_bot folder se):
    python -m evals.create_dataset
"""
from app.settings import EVAL_DATASET

from langsmith import Client
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

EXAMPLES = [
    ("Lahore mein delivery kab tak aayegi?", "1-2 din mein.", "delivery-time", "faq"),
    ("Karachi delivery kitne din?", "3-5 working days.", "delivery-time", "faq"),
    ("2500 ka order hai, delivery free hogi?", "Nahi, Rs. 3000 se upar free hai; warna Rs. 200.", "delivery-charges", "faq"),
    ("JazzCash se pay kar sakta hoon?", "Nahi, sirf Cash on Delivery hai.", "payment", "faq"),
    ("Watch pasand nahi aayi, paise wapas milenge?", "Refund nahi hota, 7 din mein exchange ho sakta hai agar unused ho.", "exchange", "faq"),
    ("Strap toot gaya, warranty mein hai?", "Nahi, strap warranty mein shamil nahi; sirf machine par 6 mahine.", "warranty", "faq"),
    ("Order track kaise karoon?", "Dispatch ke baad WhatsApp par tracking number milta hai.", "order-tracking", "faq"),
    ("Wallets milte hain?", "Haan, men's leather wallets available hain.", "wallets", "faq"),
    ("Kya 50% discount chal raha hai?", "Discount ki info available nahi; team ko forward kiya jayega.", None, "edge-cases"),
    ("Mujhe python seekhni hai, help karo", "Main sirf store se related sawalon mein madad kar sakta hoon.", None, "edge-cases"),
]


if __name__ == "__main__":
    client = Client()
    if client.has_dataset(dataset_name=EVAL_DATASET):
        raise SystemExit(f"'{EVAL_DATASET}' pehle se mojood hai.")

    ds = client.create_dataset(dataset_name=EVAL_DATASET, description="Capstone support bot golden set")
    client.create_examples(
        dataset_id=ds.id,
        examples=[
            {
                "inputs": {"question": q},
                "outputs": {"answer": a, "expected_source": src},
                "metadata": {"split_name": split},
                "split": split,
            }
            for q, a, src, split in EXAMPLES
        ],
    )
    print(f"'{EVAL_DATASET}' ban gaya: {len(EXAMPLES)} examples.")
