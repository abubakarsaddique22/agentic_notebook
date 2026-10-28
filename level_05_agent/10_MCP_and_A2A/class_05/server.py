
import httpx
from mcp.server import MCPServer

# Create MCP Server
server = MCPServer("Travel MCP Server")

GEO_URL = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"


# =========================
# 1. TOOLS
# =========================

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


@server.tool()
def calculate_budget(flight_price: int, hotel_price: int) -> dict:
    """Calculate total travel budget."""

    return {
        "flight": flight_price,
        "hotel": hotel_price,
        "total": flight_price + hotel_price,
        "currency": "PKR"
    }


@server.tool()
async def get_live_weather(city: str) -> dict:
    """Get current weather using Open-Meteo API."""

    city = city.strip()

    if len(city) < 2:
        return {"success": False, "error": "Invalid city name"}

    try:
        async with httpx.AsyncClient(timeout=10) as client:

            # Step 1: Get city coordinates
            geo_response = await client.get(
                GEO_URL,
                params={"name": city, "count": 1}
            )
            geo_response.raise_for_status()

            locations = geo_response.json().get("results", [])

            if not locations:
                return {"success": False, "error": "City not found"}

            location = locations[0]

            # Step 2: Get real weather
            weather_response = await client.get(
                WEATHER_URL,
                params={
                    "latitude": location["latitude"],
                    "longitude": location["longitude"],
                    "current": "temperature_2m,relative_humidity_2m,wind_speed_10m",
                    "timezone": "auto"
                }
            )
            weather_response.raise_for_status()

            data = weather_response.json()
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

    except (httpx.HTTPError, KeyError, ValueError) as error:
        return {
            "success": False,
            "error": str(error)
        }


# =========================
# 2. RESOURCES
# =========================

@server.resource("travel://preferences")
def travel_preferences() -> str:
    """Traveler preferences."""

    return """
    Airline: Emirates
    Seat: Window
    Class: Economy
    Hotel: 4-star
    Max Budget: 200000 PKR
    """


@server.resource("city://{city}/guide")
def city_guide(city: str) -> str:
    """City travel guide."""

    return f"""
    Destination: {city}
    Hotel: Near business center
    Transport: Airport taxi
    Check weather before traveling.
    """


# =========================
# 3. PROMPTS
# =========================

@server.prompt()
def plan_business_trip(destination: str, days: str) -> str:
    """Generate business trip planning prompt."""

    return f"""
    Plan a {days}-day business trip to {destination}.

    1. Follow traveler preferences.
    2. Read city guide.
    3. Search demo flights.
    4. Check current weather.
    5. Calculate flight + hotel budget.
    6. Do not claim a booking happened.
    7. If weather fails, explain the error.
    """


# =========================
# 4. RUN SERVER
# =========================

if __name__ == "__main__":
    server.run(
        transport="streamable-http",
        host="127.0.0.1",
        port=8001,
        stateless_http=True,
        json_response=True
    )
