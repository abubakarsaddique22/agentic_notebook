"""
A.6 + A.7 Import ke tareeqe aur __name__
========================================
    python -m scripts.a6_import_styles

Notebook mein sys.path.insert(...) karna parta tha. Yahan zaroorat nahi:
`python -m` folder ki root ko khud search path mein daal deta hai.
Theory: NOTES_A_modules.md (A.6, A.7)
"""
import sys

import bot                                   # poora package
from bot import BotConfig, Conversation      # __init__.py wala shortcut
from bot import tools                        # poora module
from bot.pricing import order_total          # specific function

print("Version          :", bot.__version__)
print("Package kahan hai:", bot.__file__)

c = Conversation("923001234567", "test")
c.add("user", "Salam")
print("Conversation     :", c.to_api_format())
print("Order id nikala  :", tools.extract_order_id("mera order 1042 hai"))
print("Default config   :", BotConfig().model)

print("\n--- __name__ ---")
import bot.main                              # import hua, lekin us ka demo loop NAHI chala
print("bot.main ka __name__ :", bot.main.__name__)
print("Is script ka __name__:", __name__)     # python -m se chalaya to "__main__"

print("\n--- sys.path (Python yahan modules dhoondta hai), pehli 3 jagahein ---")
for p in sys.path[:3]:
    print("  ", p or "(current folder)")
