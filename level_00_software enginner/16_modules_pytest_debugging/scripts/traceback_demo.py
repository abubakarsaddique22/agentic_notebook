"""
C.1 Traceback bina crash ke dekhna (try/except + traceback.print_exc)
=====================================================================
    python -m scripts.traceback_demo

Production mein yahi kaam logger.exception() karta hai (C.2).
"""
import traceback

from bot.tools import get_order_status

try:
    get_order_status(None)
except AttributeError:
    traceback.print_exc()

print("\nProgram chalta raha (crash nahi hua)")
