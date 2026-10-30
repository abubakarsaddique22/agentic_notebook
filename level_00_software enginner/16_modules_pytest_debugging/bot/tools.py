"""Bot ke tools: order status waghera."""
import logging
import re
from dataclasses import dataclass

logger = logging.getLogger(__name__)

FAKE_ORDERS = {
    "1042": "Shipped - TCS tracking ABC123",
    "1043": "Processing - kal dispatch hoga",
}


@dataclass
class ToolResult:
    tool_name: str
    success: bool
    data: str | None = None
    error: str | None = None

    def to_text(self) -> str:
        return self.data if self.success else f"Maazrat, {self.error}"


def extract_order_id(text: str) -> str | None:
    """Message mein se 4 digit order number nikaalo."""
    match = re.search(r"\b(\d{4})\b", text)
    return match.group(1) if match else None


def get_order_status(order_id: str) -> ToolResult:
    order_id = order_id.strip()
    if order_id in FAKE_ORDERS:
        return ToolResult("get_order_status", True, data=FAKE_ORDERS[order_id])
    logger.warning("Order nahi mila: %s", order_id)
    return ToolResult("get_order_status", False, error=f"order {order_id} nahi mila")
