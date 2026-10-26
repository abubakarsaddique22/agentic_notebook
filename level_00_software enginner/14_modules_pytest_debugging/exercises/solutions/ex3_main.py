"""SOLUTION 3 (part 1): is file ke content se bot/main.py ko replace kar dein.
Bot ka entry point: message aata hai, jawab jaata hai."""
import logging

from bot.config import BotConfig
from bot.faq import answer_faq
from bot.llm import ask_llm
from bot.models import Conversation
from bot.tools import extract_order_id, get_order_status

logger = logging.getLogger(__name__)


def handle_message(convo: Conversation, text: str, config: BotConfig) -> str:
    logger.info("Naya message: %r", text)
    convo.add("user", text)

    order_id = extract_order_id(text)
    if "order" in text.lower() and order_id:
        reply = get_order_status(order_id).to_text()
    elif (faq := answer_faq(text)) is not None:            # FAQ pehle, LLM baad mein
        reply = faq
    else:
        reply = ask_llm(convo.to_api_format(), config)

    convo.add("assistant", reply)
    return reply


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)-8s %(name)s: %(message)s")
    cfg = BotConfig()
    convo = Conversation("923001234567", cfg.system_prompt, max_history=cfg.max_history)
    for msg in ["Mera order 1042 kahan hai?", "COD hai?", "Salam"]:
        print("User:", msg)
        print("Bot :", handle_message(convo, msg, cfg))
