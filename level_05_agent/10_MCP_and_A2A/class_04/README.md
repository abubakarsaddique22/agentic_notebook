# Class 4 — MCP Streamable HTTP + LangChain AI Agent

## Goal
Class 3 ke STDIO-based Travel MCP Agent ko Streamable HTTP transport par shift karna. Server ko alag terminal mein run karna aur client/agent ko URL `http://127.0.0.1:8001/mcp` se connect karna.

## Architecture

```text
User -> LangChain Agent (Groq) -> MCPAdapter (HTTP URL)
                                   -> Travel MCP Server :8001/mcp
                                      |- search_flights (demo)
                                      |- calculate_budget
                                      |- travel://preferences
                                      |- city://{city}/guide
                                      |- plan_business_trip prompt
```

## Key Concepts
- **STDIO:** client server process launch karta hai, stdin/stdout pipes par data transfer.
- **Streamable HTTP:** server independent HTTP endpoint provide karta hai, client URL se connect karta hai.
- **Tools:** executable functions.
- **Resources:** context, e.g. travel preferences.
- **Resource templates:** dynamic URI, e.g. `city://Dubai/guide`.
- **Prompts:** reusable instructions; automatically LLM mein nahi jaate.
- **MCPAdapter:** MCP tools ko LangChain-compatible tools mein convert karta hai.
- **stateless_http=True:** request-to-request MCP transport session persist nahi hota.
- **json_response=True:** each request ke liye direct JSON responses; some advanced server-client interactions unavailable.

## Setup (PowerShell)

From `MCP_Practical` root:

```powershell
.venv\Scripts\Activate.ps1
python -m pip install -U "mcp[cli]" "langchain[mcp]" langchain-groq python-dotenv
```

Root `.env`:

```dotenv
GROQ_API_KEY=your_actual_key
```

## server.py

```python
from mcp.server import MCPServer

server = MCPServer("Travel MCP Server")

@server.tool()
def search_flights(origin: str, destination: str) -> dict:
    """Return sample flights (not live inventory)."""
    return {"airline": "Emirates", "origin": origin, "destination": destination,
            "price": 85000, "currency": "PKR", "demo": True}

@server.tool()
def calculate_budget(flight_price: int, hotel_price: int) -> dict:
    """Calculate estimated flight and hotel cost."""
    return {"flight_price": flight_price, "hotel_price": hotel_price,
            "total": flight_price + hotel_price, "currency": "PKR"}

@server.resource("travel://preferences")
def travel_preferences() -> str:
    return """Preferred airline: Emirates
Preferred seat: Window
Preferred class: Economy
Preferred hotel: 4-star
Maximum preferred budget: 200000 PKR"""

@server.resource("city://{city}/guide")
def city_guide(city: str) -> str:
    return f"Destination: {city}\nHotel recommendation: Near business center\nTransport: Airport taxi\nReminder: Verify local rules and weather"

@server.prompt()
def plan_business_trip(destination: str, days: str) -> str:
    return (f"Plan a {days}-day business trip to {destination}. "
            "Respect travel preferences, check city context, search flights, "
            "calculate budget, and never claim demo flights are live.")

if __name__ == "__main__":
    server.run(transport="streamable-http", host="127.0.0.1", port=8001,
               stateless_http=True, json_response=True)
```

## client.py (without LLM)

```python
import asyncio
from mcp import Client
from mcp.types import TextContent, TextResourceContents

URL = "http://127.0.0.1:8001/mcp"

async def main():
    async with Client(URL) as client:
        tools = await client.list_tools()
        print("TOOLS:", [t.name for t in tools.tools])
        flight = await client.call_tool("search_flights", {"origin": "Lahore", "destination": "Dubai"})
        for item in flight.content:
            if isinstance(item, TextContent):
                print("FLIGHT:", item.text)
        for uri in ["travel://preferences", "city://Dubai/guide"]:
            r = await client.read_resource(uri)
            for item in r.contents:
                if isinstance(item, TextResourceContents):
                    print(uri, item.text)
        p = await client.get_prompt("plan_business_trip", {"destination": "Dubai", "days": "5"})
        for msg in p.messages:
            if isinstance(msg.content, TextContent):
                print("PROMPT:", msg.content.text)

if __name__ == "__main__":
    asyncio.run(main())
```

## agent.py (Groq + HTTP MCPAdapter)

```python
import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv
from mcp import Client
from mcp.types import TextContent, TextResourceContents
from langchain.mcp import MCPAdapter
from langchain.agents import create_agent
from langchain_groq import ChatGroq

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR.parent / ".env")
URL = "http://127.0.0.1:8001/mcp"
if not os.getenv("GROQ_API_KEY"):
    raise RuntimeError("GROQ_API_KEY missing")

llm = ChatGroq(model="openai/gpt-oss-20b", temperature=0, api_key=os.getenv("GROQ_API_KEY"))

async def load_context():
    async with Client(URL) as client:
        pref = await client.read_resource("travel://preferences")
        city = await client.read_resource("city://Dubai/guide")
        prompt = await client.get_prompt("plan_business_trip", {"destination": "Dubai", "days": "5"})
        def texts(result):
            return "\n".join(x.text for x in result.contents if isinstance(x, TextResourceContents))
        instructions = "\n".join(m.content.text for m in prompt.messages if isinstance(m.content, TextContent))
        return texts(pref), texts(city), instructions

async def main():
    preferences, city, instructions = await load_context()
    system_prompt = f"""You are a business travel assistant. Respond in Roman Urdu.
Preferences: {preferences}
City context: {city}
Instructions: {instructions}
Use flight and budget tools. Hotel estimate is 45000 PKR total.
Flight data is DEMO, not real live availability. Never claim booking confirmed."""
    config = {"mcpServers": {"travel": {"url": URL}}}
    async with MCPAdapter(config) as adapter:
        tools = await adapter.list_tools()
        print("DISCOVERED TOOLS:", [t.name for t in tools])
        agent = create_agent(model=llm, tools=tools, system_prompt=system_prompt)
        result = await agent.ainvoke({"messages": [{"role": "user", "content":
            "Plan a 5-day Lahore to Dubai business trip. Search a flight and calculate flight + 45000 PKR hotel estimate with MCP tools."}]})
        for message in result["messages"]:
            print(type(message).__name__, message.content)
            for call in getattr(message, "tool_calls", []) or []:
                print("TOOL:", call["name"], "ARGS:", call["args"])
        print("FINAL:", result["messages"][-1].content)

if __name__ == "__main__":
    asyncio.run(main())
```

## Run — 2 terminals

Terminal 1 (server, leave open):

```powershell
cd MCP_Practical\class_04
python server.py
```

Terminal 2 (client then agent):

```powershell
cd MCP_Practical\class_04
python client.py
python agent.py
```

## Expected Behavior
- Client discovers `search_flights`, `calculate_budget`.
- Resource read returns preferences and city guide.
- Prompt read returns instructions.
- Agent discovers tools, invokes them as needed, and summarizes sample trip costs.
- 85000 + 45000 = 130000 PKR is only a **demo** combined flight+hotel estimate.

## Common Issues
- `Connection refused`: start server first; port and URL check karo.
- `Address already in use`: port 8001 pe previous server chal raha hai, use stop karo ya port change karo.
- `404`: HTTP endpoint exactly `/mcp` use karo.
- `401`/API key: `.env` path and key check karo.
- `ModuleNotFoundError`: correct `.venv` activate karke dependencies install karo.
- Tool result nahi mila: agent message flow inspect karo; model tool calls probabilistic hain.

## Practice
1. Port 8001 se 8010 change karke server/client/agent update karo.
2. `city://London/guide` resource read karo.
3. `calculate_daily_cost(total, days)` tool banao.
4. Server stop karke client error observe karo, phir restart karo.

## Security
`127.0.0.1` local host hai, public internet ke liye nahi. Production mein HTTPS, authentication/authorization, rate limits, logging, and secrets management chahiye. Arbitrary external MCP servers par trust mat karo.

## Next Class
Class 5: Open-Meteo live weather API ko MCP Tool ke through use karna, error handling aur real external HTTP requests.

## References
- https://py.sdk.modelcontextprotocol.io/run/
- https://reference.langchain.com/python/langchain/mcp/
