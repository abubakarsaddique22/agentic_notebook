"""
Golden dataset for the capstone bot (idempotent — stable ids).

Chalao (10_capstone_support_bot folder se):
    python -m evals.create_dataset
"""
from app.settings import EVAL_DATASET, langfuse

# (id, question, reference answer, expected FAQ source, split)
EXAMPLES = [
    ("cap-lahore-delivery", "Lahore mein delivery kab tak aayegi?", "1-2 din mein.", "delivery-time", "faq"),
    ("cap-karachi-delivery", "Karachi delivery kitne din?", "3-5 working days.", "delivery-time", "faq"),
    ("cap-free-delivery", "2500 ka order hai, delivery free hogi?", "Nahi, Rs. 3000 se upar free hai; warna Rs. 200.", "delivery-charges", "faq"),
    ("cap-jazzcash", "JazzCash se pay kar sakta hoon?", "Nahi, sirf Cash on Delivery hai.", "payment", "faq"),
    ("cap-refund", "Watch pasand nahi aayi, paise wapas milenge?", "Refund nahi hota, 7 din mein exchange ho sakta hai agar unused ho.", "exchange", "faq"),
    ("cap-strap", "Strap toot gaya, warranty mein hai?", "Nahi, strap warranty mein shamil nahi; sirf machine par 6 mahine.", "warranty", "faq"),
    ("cap-track", "Order track kaise karoon?", "Dispatch ke baad WhatsApp par tracking number milta hai.", "order-tracking", "faq"),
    ("cap-wallets", "Wallets milte hain?", "Haan, men's leather wallets available hain.", "wallets", "faq"),
    ("cap-discount", "Kya 50% discount chal raha hai?", "Discount ki info available nahi; team ko forward kiya jayega.", None, "edge-cases"),
    ("cap-python", "Mujhe python seekhni hai, help karo", "Main sirf store se related sawalon mein madad kar sakta hoon.", None, "edge-cases"),
]


if __name__ == "__main__":
    try:
        langfuse.get_dataset(EVAL_DATASET)
        print(f"'{EVAL_DATASET}' mojood hai — items update honge.")
    except Exception:
        langfuse.create_dataset(name=EVAL_DATASET, description="Capstone support bot golden set")
        print(f"'{EVAL_DATASET}' ban gaya.")

    for item_id, q, a, src, split in EXAMPLES:
        langfuse.create_dataset_item(
            dataset_name=EVAL_DATASET,
            id=item_id,
            input={"question": q},
            expected_output={"answer": a, "expected_source": src},
            metadata={"split": split},
        )
    print(f"{len(EXAMPLES)} items upsert ho gaye.")
