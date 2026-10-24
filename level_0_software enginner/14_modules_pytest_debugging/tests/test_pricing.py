"""Pricing tests. Shuru mein in mein se 3 FAIL honge (bot/pricing.py mein bug hai).
Ye Part C.4 ka kaam hai: bug dhoondo, theek karo, phir sab pass."""
import pytest

from bot.pricing import DELIVERY_FEE, apply_discount, order_total


def test_no_discount():
    assert order_total([(1000, 2)]) == 2000 + DELIVERY_FEE


@pytest.mark.parametrize("price, percent, expected", [
    (1000, 0, 1000),
    (1000, 10, 900),
    (4500, 20, 3600),
])
def test_apply_discount(price, percent, expected):
    assert apply_discount(price, percent) == expected


def test_total_with_discount():
    # 1000 ki watch, 10% discount -> 900, + 200 delivery = 1100
    assert order_total([(1000, 1)], discount_percent=10) == 1100


# Bug theek karne ke baad yahan REGRESSION TEST jorein (NOTES_C_debugging.md, qadam 5)
