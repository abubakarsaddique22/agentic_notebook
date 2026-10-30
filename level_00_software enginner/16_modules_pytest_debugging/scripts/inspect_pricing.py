"""
C.4 Bug hunt, qadam 3 (Inspect): pricing ki values khud dekhna
==============================================================
    python -m scripts.inspect_pricing

VS Code mein yahi kaam bot/pricing.py ki return line par breakpoint (F9) laga kar,
aur tests/test_pricing.py ko "Debug Test" se chala kar hota hai.
"""
from bot.pricing import apply_discount

price, discount_percent = 1000, 10

print("apply_discount(1000, 10)    =", apply_discount(price, discount_percent))
print("price * discount_percent    =", price * discount_percent)
print("Hum chahte the (10% of 1000)=", price * discount_percent / 100)
print("\nClue: 10 ko 10% ki tarah use karna hai, lekin code isay 1000% bana raha hai...")
