
import httpx
from mcp.server import MCPServer

# 1. Create MCP Server
server = MCPServer("Travel MCP Server")

GEO_URL = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"


# =========================
# 2. MCP TOOLS
# =========================

@server.tool()
def search_flights(origin: str, destination: str) -> dict:
    """Return sample flight data."""

    return {
        "airline": "Emirates",
        "origin": origin,
        "destination": destination,
        "price": 85000,
        "currency": "PKR",
        "demo": True
    }


@server.tool()
def calculate_budget(flight_price: int, hotel_price: int) -> dict:
    """Calculate total travel budget."""

    return {
        "flight_price": flight_price,
        "hotel_price": hotel_price,
        "total": flight_price + hotel_price,
        "currency": "PKR"
    }


@server.tool()
async def get_live_weather(city: str) -> dict:
    """Get real weather using Open-Meteo API."""

    city = city.strip()

    if len(city) < 2:
        return {"success": False, "error": "Invalid city"}

    try:
        async with httpx.AsyncClient(timeout=10) as client:

            # Step 1: Find city coordinates
            response = await client.get(
                GEO_URL,
                params={
                    "name": city,
                    "count": 1
                }
            )

            response.raise_for_status()

            locations = response.json().get("results", [])

            if not locations:
                return {"success": False, "error": "City not found"}

            location = locations[0]

            # Step 2: Get real weather
            response = await client.get(
                WEATHER_URL,
                params={
                    "latitude": location["latitude"],
                    "longitude": location["longitude"],
                    "current": "temperature_2m,relative_humidity_2m,wind_speed_10m",
                    "timezone": "auto"
                }
            )

            response.raise_for_status()

            data = response.json()
            current = data["current"]

            return {
                "success": True,
                "source": "Open-Meteo",
                "city": location["name"],
                "country": location.get("country"),
                "time": current["time"],
                "timezone": data["timezone"],
                "temperature_c": current["temperature_2m"],
                "humidity_percent": current["relative_humidity_2m"],
                "wind_speed_kmh": current["wind_speed_10m"]
            }

    except (httpx.HTTPError, ValueError, KeyError) as error:
        return {
            "success": False,
            "error": str(error)
        }


# =========================
# 3. MCP RESOURCES
# =========================

@server.resource("travel://preferences")
def travel_preferences() -> str:
    """Traveler preferences."""

    return """
    Preferred Airline: Emirates
    Preferred Seat: Window
    Preferred Class: Economy
    Preferred Hotel: 4-star
    """


@server.resource("city://{city}/guide")
def city_guide(city: str) -> str:
    """Basic city travel guide."""

    return f"""
    Destination: {city}
    Check visa requirements.
    Check local transport.
    Check hotel location.
    Check travel rules.
    """


# =========================
# 4. MCP PROMPT
# =========================

@server.prompt()
def plan_business_trip(destination: str, days: str) -> str:
    """Business trip planning instructions."""

    return f"""
    Plan a {days}-day business trip to {destination}.

    1. Check company policies.
    2. Check current weather.
    3. Search demo flights.
    4. Calculate travel budget.
    5. Never claim a booking is confirmed.
    """


# =========================
# 5. RUN SERVER
# =========================

if __name__ == "__main__":
    server.run(
        transport="streamable-http",
        host="127.0.0.1",
        port=8001,
        stateless_http=True,
        json_response=True
    )
