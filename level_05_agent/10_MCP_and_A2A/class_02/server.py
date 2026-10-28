
from mcp.server import MCPServer

# ==================================================
# MCP SERVER
# ==================================================

server = MCPServer("Travel MCP Server")


# ==================================================
# 1. TOOL = DO
# ==================================================

@server.tool()
def search_flights(origin: str, destination: str) -> dict:
    """Return demo flight information."""

    return {
        "airline": "Emirates",
        "origin": origin,
        "destination": destination,
        "price": 85000,
        "currency": "PKR",
        "demo": True
    }


# ==================================================
# 2. RESOURCE = FIXED KNOWLEDGE
# ==================================================

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


# ==================================================
# 3. RESOURCE TEMPLATE = DYNAMIC KNOWLEDGE
# ==================================================

@server.resource("city://{city}/guide")
def city_guide(city: str) -> str:
    """Return basic city-specific travel guidance."""

    return f"""
City: {city}
Recommended hotel: Near business center
Transport: Use airport taxi
Important: Check weather and local rules
""".strip()


# ==================================================
# 4. PROMPT = REUSABLE INSTRUCTIONS
# ==================================================

@server.prompt()
def plan_business_trip(destination: str, days: str) -> str:
    """Generate instructions for planning a trip."""

    return f"""
Plan a {days}-day business trip to {destination}.

Instructions:
1. Check travel preferences.
2. Read the destination city guide.
3. Search suitable flights.
4. Recommend a hotel category.
5. Estimate the travel budget.
6. Provide a final itinerary.
""".strip()


# ==================================================
# START SERVER USING STDIO
# ==================================================

if __name__ == "__main__":
    server.run()
