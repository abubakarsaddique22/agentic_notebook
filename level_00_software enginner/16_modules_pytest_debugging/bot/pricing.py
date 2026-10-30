"""Order ka bill calculate karna.

🐞 IS FILE MEIN JAAN BOOJH KAR EK BUG HAI.
Abhi dhoondne ki koshish na karein. Part C.4 (NOTES_C_debugging.md) mein
tests aur debugging se pakrein ge aur khud theek karein ge.
"""

DELIVERY_FEE = 200


def apply_discount(price: float, discount_percent: float) -> float:
    """discount_percent: 10 ka matlab 10%."""
    return price - price * discount_percent


def order_total(items: list[tuple[int, int]], discount_percent: float = 0) -> float:
    """items: [(price, qty), ...]. Discount ke baad delivery fee jurti hai."""
    subtotal = sum(price * qty for price, qty in items)
    return apply_discount(subtotal, discount_percent) + DELIVERY_FEE
