
from mcp.server import MCPServer

# ============================================
# MCP SERVER
# ============================================

server = MCPServer("Travel MCP Server")


# ============================================
# TOOL 1: SEARCH FLIGHTS
# ============================================

@server.tool()
def search_flights(
    origin: str,
    destination: str
) -> dict:
    """Return demo flight information."""

    return {
        "airline": "Emirates",
        "origin": origin,
        "destination": destination,
        "price": 85000,
        "currency": "PKR",
        "demo": True
    }


# ============================================
# TOOL 2: CALCULATE BUDGET
# ============================================

@server.tool()
def calculate_budget(
    flight_price: int,
    hotel_price: int
) -> dict:
    """Calculate flight + hotel cost."""

    total = flight_price + hotel_price

    return {
        "flight_price": flight_price,
        "hotel_price": hotel_price,
        "total": total,
        "currency": "PKR"
    }


# ============================================
# RESOURCE: TRAVEL PREFERENCES
# ============================================

@server.resource("travel://preferences")
def travel_preferences() -> str:
    """Return traveler preferences."""

    return """
Preferred airline: Emirates
Preferred seat: Window
Preferred class: Economy
Preferred hotel: 4-star
Maximum preferred budget: 200000 PKR
""".strip()


# ============================================
# RESOURCE TEMPLATE: CITY GUIDE
# ============================================

@server.resource("city://{city}/guide")
def city_guide(city: str) -> str:
    """Return basic destination guidance."""

    return f"""
Destination: {city}
Hotel recommendation: Near business center
Transport: Airport taxi
Reminder: Verify local rules and weather
""".strip()


# ============================================
# PROMPT: BUSINESS TRIP
# ============================================

@server.prompt()
def plan_business_trip(
    destination: str,
    days: str
) -> str:
    """Reusable business travel instructions."""

    return f"""
Plan a {days}-day business trip to {destination}.

Instructions:
1. Respect travel preferences.
2. Use destination context.
3. Search flights using MCP tool.
4. Calculate estimated trip cost.
5. Provide a final itinerary.
6. Never claim demo flights are live.
""".strip()


# ============================================
# RUN STREAMABLE HTTP SERVER
# ============================================

if __name__ == "__main__":

    server.run(
        transport="streamable-http",
        host="127.0.0.1",
        port=8001,
        stateless_http=True,
        json_response=True
    )
