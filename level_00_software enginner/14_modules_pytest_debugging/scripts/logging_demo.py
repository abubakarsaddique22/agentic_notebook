"""
C.2 print ki jagah logging: levels, format, file handler
========================================================
    python -m scripts.logging_demo

Ye bot.log file bhi banaye gi (folder ki root mein).
Theory: NOTES_C_debugging.md (C.2)
"""
import logging
from pathlib import Path

from bot import tools

# basicConfig sirf ENTRY POINT par ek baar (yahan, ya main.py ke __main__ block mein)
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("logging_demo")

print("--- 1. Har level ---")
log.debug("Prompt tayyar: %s", "Tum support agent ho...")
log.info("Message aaya from %s", "923001234567")
log.warning("Order nahi mila: %s", "9999")

try:
    {"choices": []}["choices"][0]
except IndexError:
    log.exception("LLM response khali aaya")   # ERROR + poora traceback

# Hamare module (bot.tools) ka logger bhi isi config se kaam kar raha hai:
tools.get_order_status("7777")

print("\n--- 2. Level WARNING kar diya: DEBUG/INFO gayab, code mein kuch hatana nahi para ---")
logging.getLogger().setLevel(logging.WARNING)
log.info("Ye nazar nahi aaye ga")
log.warning("Ye nazar aaye ga")

print("\n--- 3. Logs file mein save karna (production bot ke liye) ---")
log_file = Path("bot.log")
file_handler = logging.FileHandler(log_file, encoding="utf-8")
file_handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s"))
logging.getLogger().addHandler(file_handler)

log.error("Shopify API timeout (demo)")

file_handler.close()
logging.getLogger().removeHandler(file_handler)
print("bot.log ka content:")
print(log_file.read_text(encoding="utf-8"))
