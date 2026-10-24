"""SOLUTION 1: is file ko copy kar ke bot/faq.py bana dein.
Aam sawalon ke fixed jawab (LLM call bachane ke liye)."""
import logging

logger = logging.getLogger(__name__)

FAQ = {
    "cod": "Ji, hum sirf Cash on Delivery lete hain.",
    "delivery": "Lahore mein 2 din, baqi Pakistan mein 3-5 din.",
    "return": "Delivery ke 7 din ke andar return ho sakta hai.",
}


def answer_faq(text: str) -> str | None:
    lowered = text.lower()
    for keyword, answer in FAQ.items():
        if keyword in lowered:
            logger.info("FAQ match: %s", keyword)
            return answer
    return None
