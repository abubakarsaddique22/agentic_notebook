"""
C.1 Stack trace parhna: ye script jaan boojh kar CRASH hoti hai
==============================================================
    python -m scripts.crash_demo

Traceback NEECHE SE UPAR parhein. Theory: NOTES_C_debugging.md (C.1)
Exercise 4 mein isay khud theek karna hai.
"""
from bot.tools import extract_order_id, get_order_status


def reply_for(text):
    order_id = extract_order_id(text)     # "Salam" mein order id nahi -> None
    return get_order_status(order_id)     # None pass ho gaya!


print(reply_for("Salam"))
