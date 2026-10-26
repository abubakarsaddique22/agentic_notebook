"""
Prompts banana, versions aur labels.

Same naam se create_prompt dobara = NAYA VERSION (purana delete nahi hota).
"""
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from langfuse import get_client  # noqa: E402

langfuse = get_client()

FAQ_HINT = "Delivery 1-2 din (Lahore), 3-5 din baqi Pakistan. Sirf COD. 7 din exchange. 6 mahine warranty."

if __name__ == "__main__":
    # ---- 1) Text prompt ----
    text_prompt = langfuse.create_prompt(
        name="product-description",
        type="text",
        prompt="{{product_name}} ke liye 2 line ki Roman Urdu product description likho. Tone: {{tone}}.",
        labels=["production"],
        commit_message="first version",
    )
    print(f"text prompt: {text_prompt.name} v{text_prompt.version}")

    # ---- 2) Chat prompt v1 (seedha production) ----
    v1 = langfuse.create_prompt(
        name="watch-support",
        type="chat",
        prompt=[
            {"role": "system", "content": "You are a support agent for {{store_name}}. FAQ:\n{{faq}}"},
            {"role": "user", "content": "{{question}}"},
        ],
        labels=["production"],
        config={"model": "gpt-4o-mini", "temperature": 0.7},  # model settings bhi prompt ke saath
        commit_message="v1: simple prompt",
    )
    print(f"chat prompt: {v1.name} v{v1.version} labels={v1.labels}")

    # ---- 3) Chat prompt v2 — sirf staging (abhi production nahi) ----
    v2 = langfuse.create_prompt(
        name="watch-support",
        type="chat",
        prompt=[
            {
                "role": "system",
                "content": (
                    "You are the customer support agent of {{store_name}}.\n"
                    "Rules: answer ONLY from the FAQ, reply in Roman Urdu, max 2 sentences, "
                    "politely refuse non-store questions.\n\nFAQ:\n{{faq}}"
                ),
            },
            {"role": "user", "content": "{{question}}"},
        ],
        labels=["staging"],
        config={"model": "gpt-4o-mini", "temperature": 0},
        commit_message="v2: strict rules + Roman Urdu",
    )
    print(f"chat prompt: {v2.name} v{v2.version} labels={v2.labels}")

    # ---- 4) Test ke baad v2 ko production par promote (UI se bhi ho sakta hai) ----
    # Uncomment karke chalao jab v2 se khush ho:
    # langfuse.update_prompt(name="watch-support", version=v2.version, new_labels=["production"])
    # print("v2 ab production hai")

    print("\nUI: Prompts -> watch-support -> dono versions aur labels dekho.")
