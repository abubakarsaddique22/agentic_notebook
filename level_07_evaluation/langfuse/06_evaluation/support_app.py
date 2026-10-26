"""
Jis app ko hum evaluate karenge — chhota FAQ support bot.

  v1 — loose (lamba, off-topic bhi jawab de deta hai)
  v2 — strict (sirf FAQ, short, off-topic politely mana)

Evaluation se SABIT karenge ke v2 behtar hai — andaze se nahi.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from langfuse import observe  # noqa: E402
from langfuse.openai import OpenAI  # noqa: E402

MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
client = OpenAI()

FAQ = """
- Delivery: Lahore mein 1-2 din, baqi Pakistan mein 3-5 working days.
- Delivery charges: Rs. 3000 se upar order par free, warna Rs. 200.
- Payment: Sirf Cash on Delivery (COD). Online/card/crypto payment nahi hoti.
- Exchange: Delivery ke 7 din ke andar, product unused ho to exchange ho sakta hai. Refund nahi.
- Warranty: Watch machine par 6 mahine ki warranty.
"""

PROMPTS = {
    "v1": "You are a helpful assistant for a watch store. Here is some info:\n{faq}",
    "v2": (
        "You are the customer support agent of a watch store.\n"
        "Rules:\n"
        "1. Answer ONLY using the FAQ below. If the answer is not in the FAQ, say you can only help "
        "with store-related questions.\n"
        "2. Reply in Roman Urdu, maximum 2 short sentences.\n"
        "3. Never invent prices, policies or payment methods.\n\n"
        "FAQ:\n{faq}"
    ),
}


@observe(name="support-bot")
def support_bot(question: str, prompt_version: str = "v2") -> str:
    system = PROMPTS[prompt_version].format(faq=FAQ)
    resp = client.chat.completions.create(
        model=MODEL,
        temperature=0,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": question}],
        name=f"support-answer-{prompt_version}",
    )
    return resp.choices[0].message.content


if __name__ == "__main__":
    from langfuse import get_client

    print(support_bot("Bitcoin se payment ho sakti hai?", "v1"))
    print(support_bot("Bitcoin se payment ho sakti hai?", "v2"))
    get_client().flush()
