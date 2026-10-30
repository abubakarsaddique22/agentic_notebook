"""SOLUTION 2: is file ko copy kar ke tests/test_faq.py bana dein.
(Yahan exercises/ folder mein ye pytest ke testpaths se bahar hai, is liye khud nahi chalti.)"""
import pytest

from bot.faq import answer_faq


@pytest.mark.parametrize("text, must_contain", [
    ("Kya COD hai?", "Cash on Delivery"),
    ("cod chalta hai?", "Cash on Delivery"),
    ("Delivery kab tak?", "2 din"),
    ("RETURN policy?", "7 din"),
])
def test_faq_match(text, must_contain):
    assert must_contain in answer_faq(text)


def test_faq_no_match():
    assert answer_faq("Salam bhai") is None
