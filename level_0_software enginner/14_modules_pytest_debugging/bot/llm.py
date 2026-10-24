"""LLM se baat karne wala module (yahan fake).

Asli project mein yahan OpenAI/Anthropic ki API call hoti hai. time.sleep(2) se
"slow aur mehngi call" ka natak kiya hai. Tests mein isay MOCK karte hain (Part B.8).
"""
import logging
import time

from bot.config import BotConfig

logger = logging.getLogger(__name__)


def ask_llm(messages: list[dict], config: BotConfig) -> str:
    """Asli project mein yahan API call hogi (paise + waqt lagta hai)."""
    logger.info("LLM call: model=%s, messages=%d", config.model, len(messages))
    time.sleep(2)  # slow network call ka natak
    last = messages[-1]["content"]
    return f"(LLM ka jawab) Aap ne kaha: '{last}'. Main aap ki kya madad karoon?"
