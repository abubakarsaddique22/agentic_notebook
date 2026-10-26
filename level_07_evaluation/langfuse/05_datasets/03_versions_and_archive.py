"""
Splits, updates, archive aur versions.

Splits:   Langfuse mein built-in nahi -> metadata["split"] se filter
Update:   same id ke saath create_dataset_item -> item update (naya version banta hai)
Archive:  status="ARCHIVED" -> item future experiments mein nahi aata, lekin history mein rehta hai
Versions: get_dataset(name, version=<datetime>) -> dataset us waqt jaisa tha
          (evals ko fixed data par chalane ke liye — taake scores compare ho sakein)
"""
import time
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from langfuse import get_client  # noqa: E402

DATASET_NAME = "watch-support-qa"


def set_status(langfuse, item, status: str) -> None:
    """Upsert mein purana data bhi bhejo — sirf status badalna hai, input/output nahi khona."""
    langfuse.create_dataset_item(
        dataset_name=DATASET_NAME,
        id=item.id,
        input=item.input,
        expected_output=item.expected_output,
        metadata=item.metadata,
        status=status,
    )


def active_count(ds) -> int:
    return sum(1 for it in ds.items if str(it.status).upper().endswith("ACTIVE"))


if __name__ == "__main__":
    langfuse = get_client()

    # 1) Split filter
    dataset = langfuse.get_dataset(DATASET_NAME)
    edge = [it for it in dataset.items if (it.metadata or {}).get("split") == "edge-cases"]
    print(f"edge-cases: {len(edge)} items")
    for it in edge:
        print("  -", it.input["question"])

    # 2) Abhi ka waqt yaad rakho (yeh hamara "v1 snapshot" hai)
    snapshot_time = datetime.now(timezone.utc)
    time.sleep(2)

    # 3) Ek naya item add karo + ek purana archive karo
    langfuse.create_dataset_item(
        dataset_name=DATASET_NAME,
        id="wsqa-wallets",
        input={"question": "Kya wallets bhi milte hain?"},
        expected_output={"answer": "Haan, men's leather wallets available hain."},
        metadata={"category": "products", "split": "test"},
    )
    offtopic = next(it for it in dataset.items if it.id == "wsqa-edge-offtopic")
    set_status(langfuse, offtopic, "ARCHIVED")
    print("\n'wsqa-wallets' add kiya, 'wsqa-edge-offtopic' archive kiya.")

    # 4) Latest vs snapshot
    latest = langfuse.get_dataset(DATASET_NAME)
    old = langfuse.get_dataset(DATASET_NAME, version=snapshot_time)
    print(f"Latest version  : {len(latest.items)} items ({active_count(latest)} active)")
    print(f"Snapshot version: {len(old.items)} items ({active_count(old)} active)")

    # 5) Wapas restore (taake folder 06 mein sab items milein)
    set_status(langfuse, offtopic, "ACTIVE")
    print("\n'wsqa-edge-offtopic' wapas ACTIVE kar diya.")
