
from mcp.server import MCPServer

# MCP Server
server = MCPServer("Travel MCP Server")


# ==========================================
# TOOLS
# ==========================================

@server.tool()
def search_flights(origin: str, destination: str) -> dict:
    """Return demo flight information."""
    return {
        "airline": "Emirates",
        "origin": origin,
        "destination": destination,
        "price": 85000,
        "currency": "PKR",
        "demo": True,
    }


@server.tool()
def calculate_budget(
    flight_price: int,
    hotel_price: int
) -> int:
    """Calculate estimated travel cost."""
    return flight_price + hotel_price


# ==========================================
# FIXED RESOURCE
# ==========================================

@server.resource("travel://preferences")
def travel_preferences() -> str:
    """Return traveler preferences."""
    return """
Preferred airline: Emirates
Preferred seat: Window
Preferred flight class: Economy
Preferred hotel: 4-star
Travel budget: 200000 PKR
""".strip()


# ==========================================
# RESOURCE TEMPLATE
# ==========================================

@server.resource("city://{city}/guide")
def city_guide(city: str) -> str:
    """Return city-specific travel guidance."""
    return f"""
City: {city}
Recommended hotel: Near business center
Transport: Use airport taxi
Important: Check weather and local rules
""".strip()


# ==========================================
# MCP PROMPT
# ==========================================

@server.prompt()
def plan_business_trip(
    destination: str,
    days: str
) -> str:
    """Generate business trip planning instructions."""
    return f"""
Plan a {days}-day business trip to {destination}.

Instructions:
1. Check travel preferences.
2. Read destination city guide.
3. Search suitable flights.
4. Recommend a hotel category.
5. Estimate travel budget.
6. Provide final itinerary.
""".strip()


# ==========================================
# START STDIO SERVER
# ==========================================

if __name__ == "__main__":
    server.run(transport="stdio")
