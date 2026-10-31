"""
=====================================================================
 CLASS 12 | store_mcp_server.py   (ise khud run karne ki zaroorat NAHI)
=====================================================================
 CONCEPT: MCP Server (Model Context Protocol)
 Kya hai : MCP ek standard hai jis se koi bhi app apne tools AI ko de
           sakti hai. Ye chhota server 2 tools deta hai. 01_mcp_tools.py
           isay khud background mein chalata hai (stdio transport).
           Yahi server Claude Desktop / Cursor bhi use kar sakte hain.
 Note    : mcp 2.x mein FastMCP ka naam MCPServer ho gaya hai.
=====================================================================
"""

from mcp.server.mcpserver import MCPServer

server = MCPServer("watch-store")

ORDERS = {"1001": "Shipped - TCS tracking 77881", "1002": "Packing - will be dispatched tomorrow", "1003": "Delivered"}


@server.tool()
def get_order_status(order_id: str) -> str:
    """Returns the status of an order by order number."""
    return ORDERS.get(order_id.strip(), f"Order {order_id} not found.")


@server.tool()
def list_categories() -> list[str]:
    """Returns the store's watch categories."""
    return ["Analog", "Chronograph", "Sports", "Minimal", "Executive"]


if __name__ == "__main__":
    server.run()      # default: stdio
