"""EASY VERSION: Travel MCP server (port 8001) + real weather tool (Open-Meteo, free, no API key)."""
import logging

import httpx
from mcp.server import MCPServer

server = MCPServer("Travel MCP Server")
logging.basicConfig(level=logging.INFO)

GEO_URL = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"


# ============================================
# TOOL 1: FLIGHTS (demo data)
# ============================================

@server.tool()
def search_flights(origin: str, destination: str) -> dict:
    """Return SAMPLE flight data; not real availability or booking."""
    return {
        "airline": "Emirates",
        "origin": origin,
        "destination": destination,
        "price": 85000,
        "currency": "PKR",
        "demo": True,
    }


# ============================================
# TOOL 2: BUDGET
# ============================================

@server.tool()
def calculate_budget(flight_price: int, hotel_price: int) -> dict:
    """Calculate demo flight plus hotel budget in PKR."""
    return {
        "flight_price": flight_price,
        "hotel_price": hotel_price,
        "total": flight_price + hotel_price,
        "currency": "PKR",
    }


# ============================================
# TOOL 3: LIVE WEATHER (real API)
# Step 1: city ka naam -> latitude/longitude
# Step 2: latitude/longitude -> abhi ka weather
# ============================================

@server.tool()
async def get_live_weather(city: str) -> dict:
    """Retrieve current weather for a city from the real Open-Meteo API."""
    city = city.strip()
    if len(city) < 2:
        return {"success": False, "error": "City name too short"}

    try:
        async with httpx.AsyncClient(timeout=10) as client:

            # Step 1: city dhoondo
            geo = await client.get(GEO_URL, params={"name": city, "count": 1})
            geo.raise_for_status()
            results = geo.json().get("results")

            if not results:
                return {"success": False, "error": f"City not found: {city}"}

            place = results[0]

            # Step 2: us jagah ka weather lo
            weather = await client.get(WEATHER_URL, params={
                "latitude": place["latitude"],
                "longitude": place["longitude"],
                "current": "temperature_2m,relative_humidity_2m,wind_speed_10m",
                "timezone": "auto",
            })
            weather.raise_for_status()
            current = weather.json()["current"]

        return {
            "success": True,
            "source": "Open-Meteo",
            "city": place["name"],
            "country": place.get("country"),
            "time": current["time"],
            "temperature_c": current["temperature_2m"],
            "humidity_percent": current["relative_humidity_2m"],
            "wind_speed_kmh": current["wind_speed_10m"],
        }

    except (httpx.HTTPError, KeyError, ValueError) as error:
        # Internet band, API down, ya data adhoora -> server crash nahi hoga
        logging.exception("Weather API call failed")
        return {"success": False, "error": f"Weather unavailable ({type(error).__name__})"}


# ============================================
# RESOURCES
# ============================================

@server.resource("travel://preferences")
def travel_preferences() -> str:
    """Fixed demo traveler preferences."""
    return (
        "Preferred airline: Emirates\n"
        "Preferred seat: Window\n"
        "Preferred class: Economy\n"
        "Preferred hotel: 4-star"
    )


@server.resource("city://{city}/guide")
def city_guide(city: str) -> str:
    """Illustrative destination advice, not a verified travel guide."""
    return f"Destination: {city}. Confirm visa, local transport, hotel location, and travel rules."


# ============================================
# PROMPT
# ============================================

@server.prompt()
def plan_business_trip(destination: str, days: str) -> str:
    """Reusable business-trip planning instructions."""
    return (
        f"Plan a {days}-day trip to {destination}. "
        "Check company policy, current weather, demo flights, budget; "
        "avoid invented booking confirmations."
    )


# ============================================
# RUN SERVER
# ============================================

if __name__ == "__main__":
    server.run(
        transport="streamable-http",
        host="127.0.0.1",
        port=8001,
        stateless_http=True,
        json_response=True,
    )