"""Bot ka entry point: message aata hai, jawab jaata hai.

Dhyan dein:
- Absolute imports: from bot.tools import ...
- logger = logging.getLogger(__name__): har module ka apna logger
- if __name__ == "__main__": neeche wala code sirf tab chale ga jab ye file DIRECTLY chalayi jaye

Chalayein (folder ki root se):   python -m bot.main
Ye FAIL hoga (try karein!):      python bot/main.py      <- NOTES_A_modules.md (A.8)
"""
import logging

from bot.config import BotConfig
from bot.llm import ask_llm
from bot.models import Conversation
from bot.tools import extract_order_id, get_order_status

logger = logging.getLogger(__name__)


def handle_message(convo: Conversation, text: str, config: BotConfig) -> str:
    logger.info("Naya message: %r", text)
    convo.add("user", text)

    order_id = extract_order_id(text)
    if "order" in text.lower() and order_id:
        reply = get_order_status(order_id).to_text()      # tool, LLM ki zaroorat nahi
    else:
        reply = ask_llm(convo.to_api_format(), config)    # baqi sab LLM

    convo.add("assistant", reply)
    return reply


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)-8s %(name)s: %(message)s")
    cfg = BotConfig()
    convo = Conversation("923001234567", cfg.system_prompt, max_history=cfg.max_history)
    for msg in ["Mera order 1042 kahan hai?", "Order 5555 ka kya hua?", "Salam"]:
        print("User:", msg)
        print("Bot :", handle_message(convo, msg, cfg))
