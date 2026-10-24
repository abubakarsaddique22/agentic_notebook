"""SOLUTION 4: is file ke content se scripts/crash_demo.py ko replace kar dein."""
import logging

from bot.tools import extract_order_id, get_order_status

logger = logging.getLogger(__name__)


def reply_for(text: str) -> str:
    order_id = extract_order_id(text)
    if order_id is None:                                   # None check
        logger.warning("Message mein order id nahi: %r", text)
        return "Order number bata dein (jaise 1042)."
    return get_order_status(order_id).to_text()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)-8s %(name)s: %(message)s")
    print(reply_for("Salam"))
    print(reply_for("order 1042"))
