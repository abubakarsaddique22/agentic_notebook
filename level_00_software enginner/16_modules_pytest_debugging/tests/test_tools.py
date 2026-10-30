"""B.7 Tools test + logs check karna (caplog)."""
import logging

import pytest

from bot.tools import extract_order_id, get_order_status


@pytest.mark.parametrize("text, expected", [
    ("Mera order 1042 kahan hai?", "1042"),
    ("order #1043", "1043"),
    ("Salam", None),
    ("phone 03001234567", None),     # 11 digit number order id nahi
])
def test_extract_order_id(text, expected):
    assert extract_order_id(text) == expected


def test_known_order():
    result = get_order_status("1042")
    assert result.success
    assert "TCS" in result.data


def test_unknown_order_logs_warning(caplog):
    with caplog.at_level(logging.WARNING):
        result = get_order_status("9999")
    assert not result.success
    assert "9999" in caplog.text
