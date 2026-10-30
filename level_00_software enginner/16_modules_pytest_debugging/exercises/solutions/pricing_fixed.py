"""SOLUTION (Part C.4 bug hunt): is file ke content se bot/pricing.py ko replace kar dein.
Phir neeche wala regression test tests/test_pricing.py ke aakhir mein jorein."""

DELIVERY_FEE = 200


def apply_discount(price: float, discount_percent: float) -> float:
    """discount_percent: 10 ka matlab 10%."""
    if not 0 <= discount_percent <= 100:
        raise ValueError("discount 0 aur 100 ke beech ho")
    return price - price * discount_percent / 100      # FIX: / 100


def order_total(items: list[tuple[int, int]], discount_percent: float = 0) -> float:
    """items: [(price, qty), ...]. Discount ke baad delivery fee jurti hai."""
    subtotal = sum(price * qty for price, qty in items)
    return apply_discount(subtotal, discount_percent) + DELIVERY_FEE


# ---------------- Regression test (tests/test_pricing.py mein jorein) ----------------
#
# @pytest.mark.parametrize("bad", [-5, 150])
# def test_invalid_discount_raises(bad):
#     with pytest.raises(ValueError):
#         apply_discount(1000, bad)
