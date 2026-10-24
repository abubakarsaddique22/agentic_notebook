"""
C.1 JSON <-> Python: loads/dumps, Urdu text, datetime
=====================================================
Server ki zaroorat NAHI.
    python -m part_c_json.c1_json_basics

Theory: part_c_json/NOTES.md (C.1)
"""
import json
import sys
from datetime import datetime

sys.stdout.reconfigure(encoding="utf-8", errors="replace")   # Windows cmd mein Urdu print ke liye

print("--- 1. JSON string -> Python dict (json.loads) ---")
text = '{"order_id": "1042", "items": [{"name": "Watch", "price": 4500}], "paid": false, "coupon": null}'
data = json.loads(text)
print(type(data), data)
print("Pehle item ka naam:", data["items"][0]["name"])
print("paid (false -> False):", data["paid"], "| coupon (null -> None):", data["coupon"])

# Khatarnak: key na ho to KeyError. .get() se default
print("Discount:", data.get("discount", 0))

print("\n--- 2. Urdu text: ensure_ascii=False ---")
msg = {"text": "آپ کا آرڈر روانہ ہو گیا", "sent_at": datetime(2026, 10, 22, 14, 30), "tags": {"urdu"}}
print(json.dumps({"text": msg["text"]}))                       # آ... kachra
print(json.dumps({"text": msg["text"]}, ensure_ascii=False))   # saaf Urdu

print("\n--- 3. datetime/set JSON mein seedhe nahi jaate ---")
try:
    json.dumps(msg)
except TypeError as e:
    print("Error:", e)


def to_json_safe(o):
    """json.dumps ko batao ke anjaan types ko kaise badle."""
    if isinstance(o, datetime):
        return o.isoformat()          # "2026-10-22T14:30:00": standard format
    if isinstance(o, set):
        return sorted(o)
    raise TypeError(type(o))


print(json.dumps(msg, default=to_json_safe, ensure_ascii=False, indent=2))
