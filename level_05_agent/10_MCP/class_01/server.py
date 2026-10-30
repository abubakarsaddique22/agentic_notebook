from mcp.server import MCPServer

# Create MCP Server
server = MCPServer("Travel MCP Server")


# Tool 1: Search flights
@server.tool()
def search_flights(origin: str, destination: str) -> dict:
    """Return sample flight information."""

    return {
        "airline": "Emirates",
        "origin": origin,
        "destination": destination,
        "price": 85000,
        "currency": "PKR",
        "demo": True
    }


# Tool 2: Calculate trip budget
@server.tool()
def calculate_budget(flight_price: int,hotel_price: int,food_price : int) -> int:
    """Calculate total travel cost."""

    return flight_price + hotel_price + food_price



# Start MCP Server using STDIO
if __name__ == "__main__":
    server.run()
