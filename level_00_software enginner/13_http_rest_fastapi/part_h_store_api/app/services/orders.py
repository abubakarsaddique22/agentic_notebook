"""Data layer. Yahan dict hai, asal mein DB ya Shopify API. Is file ko HTTP ka pata nahi."""
import re

_ORDERS = {
    "1042": {"order_id": "1042", "status": "shipped", "total_pkr": 4700, "courier": "TCS"},
    "1043": {"order_id": "1043", "status": "pending", "total_pkr": 2000, "courier": None},
    "1044": {"order_id": "1044", "status": "delivered", "total_pkr": 6700, "courier": "Leopards"},
}


def get_order(order_id: str) -> dict | None:
    return _ORDERS.get(order_id)


def list_orders(status: str | None, limit: int, offset: int) -> tuple[list[dict], int]:
    items = [o for o in _ORDERS.values() if status is None or o["status"] == status]
    return items[offset:offset + limit], len(items)


def find_order_id(text: str) -> str | None:
    match = re.search(r"\b(\d{4})\b", text)
    return match.group(1) if match else None
