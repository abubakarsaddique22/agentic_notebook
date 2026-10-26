"""
Dataset banana — code se (git mein rehta hai, team share karti hai).

Idempotent: har item ka stable `id` hai. Dobara chalao -> same items update honge, duplicate nahi.
"""
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from langfuse import get_client  # noqa: E402

DATASET_NAME = "watch-support-qa"

ITEMS = [
    # ---- normal FAQs (split: test) ----
    {
        "id": "wsqa-delivery-time",
        "input": {"question": "Delivery kitne din mein hoti hai?"},
        "expected_output": {"answer": "Lahore mein 1-2 din, baqi Pakistan mein 3-5 working days."},
        "metadata": {"category": "delivery", "split": "test"},
    },
    {
        "id": "wsqa-payment",
        "input": {"question": "Kya online payment ho sakti hai?"},
        "expected_output": {"answer": "Nahi, abhi sirf Cash on Delivery (COD) available hai."},
        "metadata": {"category": "payment", "split": "test"},
    },
    {
        "id": "wsqa-returns",
        "input": {"question": "Return ya exchange policy kya hai?"},
        "expected_output": {"answer": "Delivery ke 7 din ke andar exchange ho sakta hai agar product unused ho."},
        "metadata": {"category": "returns", "split": "test"},
    },
    {
        "id": "wsqa-delivery-charges",
        "input": {"question": "Delivery charges kitne hain?"},
        "expected_output": {"answer": "Rs. 3000 se upar order par free delivery, warna Rs. 200."},
        "metadata": {"category": "delivery", "split": "test"},
    },
    {
        "id": "wsqa-warranty",
        "input": {"question": "Kya watches par warranty hai?"},
        "expected_output": {"answer": "Haan, machine par 6 mahine ki warranty hai."},
        "metadata": {"category": "warranty", "split": "test"},
    },
    # ---- edge cases (bot ko yahan fail nahi hona chahiye) ----
    {
        "id": "wsqa-edge-bitcoin",
        "input": {"question": "Mujhe bitcoin mein payment karni hai"},
        "expected_output": {"answer": "Maazrat, sirf Cash on Delivery available hai."},
        "metadata": {"category": "payment", "split": "edge-cases"},
    },
    {
        "id": "wsqa-edge-offtopic",
        "input": {"question": "Aaj cricket match kaun jeetega?"},
        "expected_output": {"answer": "Main sirf store se related sawalon mein madad kar sakta hoon."},
        "metadata": {"category": "off-topic", "split": "edge-cases"},
    },
]


def ensure_dataset(langfuse) -> None:
    try:
        langfuse.get_dataset(DATASET_NAME)
        print(f"Dataset '{DATASET_NAME}' pehle se mojood hai — items update honge.")
    except Exception:
        langfuse.create_dataset(
            name=DATASET_NAME,
            description="Watch store support bot ke golden Q&A (FAQ + edge cases)",
            metadata={"owner": "abubakar", "domain": "ecommerce-support"},
        )
        print(f"Dataset '{DATASET_NAME}' ban gaya.")


if __name__ == "__main__":
    langfuse = get_client()
    ensure_dataset(langfuse)

    for item in ITEMS:
        langfuse.create_dataset_item(
            dataset_name=DATASET_NAME,
            id=item["id"],  # same id = upsert (update), naya id = naya item
            input=item["input"],
            expected_output=item["expected_output"],
            metadata=item["metadata"],
        )
    print(f"{len(ITEMS)} items upsert ho gaye.")

    dataset = langfuse.get_dataset(DATASET_NAME)
    print(f"Total active items: {len(dataset.items)}")
