"""
=====================================================================
 CLASS 10 | watch_mcp_server.py   (ise khud run karne ki zaroorat NAHI)
=====================================================================
 CONCEPT: MCP Server (Model Context Protocol)
 Kya hai : MCP ek standard hai jis se koi bhi app apne "tools" AI ko de
           sakti hai. Ye chhota sa MCP server 2 tools deta hai.
           01_mcp_tools.py isay khud background mein start karta hai
           ("stdio" = dono programs terminal ke input/output se baat
           karte hain).
 Note    : Ye bilkul normal Python hai — CrewAI ka code nahi. Yahi
           server Claude Desktop, Cursor waghera bhi use kar sakte hain.
=====================================================================
"""

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("watch-store")

ORDERS = {
    "1001": "Shipped - TCS tracking 77881",
    "1002": "Packing - will be dispatched tomorrow",
    "1003": "Delivered",
}


@mcp.tool()
def get_order_status(order_id: str) -> str:
    """Returns the status of an order by order number."""
    return ORDERS.get(order_id.strip(), f"Order {order_id} not found.")


@mcp.tool()
def list_watch_categories(show: str) -> list[str]:
    """Returns the watch categories in the store.

    Args:
        show: Always pass 'all'.
    """
    return ["Analog", "Chronograph", "Sports", "Minimal", "Executive"]


if __name__ == "__main__":
    mcp.run()   # default transport = stdio
