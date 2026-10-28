import asyncio
import logging
import httpx
from mcp.server import MCPServer

server = MCPServer('Travel MCP Server')
logging.basicConfig(level=logging.INFO)

@server.tool()
def search_flights(origin: str, destination: str) -> dict:
    """Return SAMPLE flight data; not real availability or booking."""
    return {'airline': 'Emirates', 'origin': origin, 'destination': destination, 'price': 85000, 'currency': 'PKR', 'demo': True}

@server.tool()
def calculate_budget(flight_price: int, hotel_price: int) -> dict:
    """Calculate demo flight plus hotel budget in PKR."""
    return {'flight_price': flight_price, 'hotel_price': hotel_price, 'total': flight_price + hotel_price, 'currency': 'PKR'}

async def fetch_json(client: httpx.AsyncClient, url: str, params: dict) -> dict:
    for attempt in range(3):
        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            if not isinstance(data, dict):
                raise ValueError('Expected JSON object')
            if data.get('error'):
                raise ValueError(str(data.get('reason', 'API error')))
            return data
        except (httpx.TimeoutException, httpx.TransportError) as exc:
            if attempt == 2:
                raise
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code not in {429, 500, 502, 503, 504} or attempt == 2:
                raise
        await asyncio.sleep(0.5 * 2 ** attempt)
    raise RuntimeError('Retry limit exceeded')

@server.tool()
async def get_live_weather(city: str) -> dict:
    """Retrieve current weather for a city from the real Open-Meteo API."""
    if len(city.strip()) < 2:
        return {'success': False, 'error': 'City name too short'}
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            geo = await fetch_json(client, 'https://geocoding-api.open-meteo.com/v1/search',
                                   {'name': city.strip(), 'count': 1, 'language': 'en', 'format': 'json'})
            locations = geo.get('results') or []
            if not locations:
                return {'success': False, 'error': f'City not found: {city}'}
            place = locations[0]
            data = await fetch_json(client, 'https://api.open-meteo.com/v1/forecast',
                                    {'latitude': place['latitude'], 'longitude': place['longitude'],
                                     'current': 'temperature_2m,relative_humidity_2m,wind_speed_10m',
                                     'timezone': 'auto'})
            current = data.get('current') or {}
            fields = ('temperature_2m', 'relative_humidity_2m', 'wind_speed_10m')
            if any(current.get(field) is None for field in fields):
                return {'success': False, 'error': 'Weather information incomplete'}
            return {'success': True, 'source': 'Open-Meteo', 'city': place['name'],
                    'country': place.get('country'), 'time': current.get('time'),
                    'timezone': data.get('timezone'), 'temperature_c': current['temperature_2m'],
                    'humidity_percent': current['relative_humidity_2m'],
                    'wind_speed_kmh': current['wind_speed_10m']}
    except (httpx.HTTPError, ValueError, KeyError) as exc:
        logging.exception('Open-Meteo call failed')
        return {'success': False, 'error': f'Weather unavailable ({type(exc).__name__})'}

@server.resource('travel://preferences')
def travel_preferences() -> str:
    """Fixed demo traveler preferences."""
    return 'Preferred airline: Emirates\nPreferred seat: Window\nPreferred class: Economy\nPreferred hotel: 4-star'

@server.resource('city://{city}/guide')
def city_guide(city: str) -> str:
    """Illustrative destination advice, not a verified travel guide."""
    return f'Destination: {city}. Confirm visa, local transport, hotel location, and travel rules.'

@server.prompt()
def plan_business_trip(destination: str, days: str) -> str:
    """Reusable business-trip planning instructions."""
    return f'Plan a {days}-day trip to {destination}. Check company policy, current weather, demo flights, budget; avoid invented booking confirmations.'

if __name__ == '__main__':
    server.run(transport='streamable-http', host='127.0.0.1', port=8001, stateless_http=True, json_response=True)
