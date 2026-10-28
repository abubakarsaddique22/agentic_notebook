# Class 05 — Real Open-Meteo API + Streamable HTTP MCP + Groq LangChain Agent

## Goal (Roman Urdu)
Class 4 ka Travel MCP HTTP server extend karo. Naya `get_live_weather(city)` tool real Open-Meteo APIs se **current** weather retrieve karega. Sample `search_flights` tool sample hi rahega. LLM tool results ke basis par travel plan banayega.

## Project files
- `server.py`: MCP HTTP server, flight demo, budget, live weather, resources, prompt
- `client.py`: Direct MCP client—without LLM—success aur invalid-city cases test karta hai
- `agent.py`: Groq + LangChain AI agent, HTTP MCPAdapter, travel resources/prompts
- `requirements.txt`: dependencies
- `.env` **project root** mein; `GROQ_API_KEY` save karo (never commit secret)

## Flow
```
User request -> LangChain agent -> MCPAdapter -> MCP HTTP server
                                  |               |
                                  |               +-> get_live_weather(city)
                                  |                       |
                                  |                       +-> Open-Meteo Geocoding API: city -> coordinates
                                  |                       +-> Open-Meteo Forecast API: coordinates -> current weather
                                  +<- structured tool result <-+
                    -> model synthesizes final answer
```

## Setup (Windows PowerShell)
Project root `MCP_Practical` mein:
```powershell
.venv\Scripts\Activate.ps1
cd class_05
python -m pip install -U -r requirements.txt
```
Root `.env` file:
```dotenv
GROQ_API_KEY=your_real_key
```
SDK: Python MCP SDK **v2** (`MCPServer`, `Client`, `MCPAdapter`). Python 3.11+ recommended.

## Run order
**Terminal 1** (class_05 folder):
```powershell
python server.py
```
Server listens on `http://127.0.0.1:8001/mcp`. Keep it running. If previous class server uses port 8001, stop it first.

**Terminal 2** (class_05 folder):
```powershell
python client.py
```
Expected: tools `search_flights`, `calculate_budget`, `get_live_weather` listed; Dubai/Lahore weather returned or meaningful error; nonexistent city returns `success: false`.

Then in Terminal 2:
```powershell
python agent.py
```
Expected: agent discovers `travel_get_live_weather`, `travel_search_flights`, `travel_calculate_budget` (prefix may depend on adapter), tool messages, and a final Roman Urdu plan. Actual weather numbers vary: never hardcode them.

## Core concepts
| Concept | Simple explanation |
|---|---|
| MCP Tool | Python callable jo MCP se discover aur execute hota hai |
| External API | MCP server Open-Meteo ko HTTP request karta hai |
| Geocoding | City ko latitude,longitude mein convert karna |
| Forecast API | Coordinates se current temperature, humidity, wind lena |
| Async | HTTP wait mein event loop ko block na karna |
| MCPAdapter | MCP tools ko LangChain-compatible tools banata hai |
| Resources | `travel://preferences`, `city://{city}/guide`: host context |
| Prompt | `plan_business_trip`: reusable guidance; host reads it explicitly |
| Groq | LLM chooses which tool(s) to call; order is not guaranteed |

## Error handling
- Empty/too-short city -> controlled `success: false`
- Unknown city -> controlled `success: false`
- Timeout/connection -> retries at 0.5s and 1s after failures (3 attempts total)
- HTTP `429`, `500`, `502`, `503`, `504` -> retry; others do not retry
- Non-JSON/malformed response or missing weather fields -> controlled failure
- Server down -> direct client connection error; start Terminal 1
- Port already in use -> stop old class_04 server or change URL + port in all three files
- Missing API key -> confirm `MCP_Practical/.env` exists

**Limits:** Geocoding currently uses first city result; identical city names can be ambiguous. Weather is data from provider at the reported observation/model time, not a real-time physical sensor reading. Sample flight is not live availability. API terms/attribution apply.

## Practice tasks
1. `get_live_weather('Karachi')` run karo and timestamp dekho.
2. Wrong city string bhejo aur observe `success: false`.
3. Internet disconnect karke retry behavior observe karo, phir restore karo.
4. `apparent_temperature` ko current parameters aur result mein add karo.
5. Agent ko flight ki jagah sirf weather ka user question do aur message flow check karo.

## Class 6 preview
Travel, Policy aur Work—3 alag MCP servers ek agent se connect karna.

## Documentation
- https://open-meteo.com/en/docs/geocoding-api
- https://open-meteo.com/en/docs
- https://py.sdk.modelcontextprotocol.io/client/
- https://py.sdk.modelcontextprotocol.io/run/
