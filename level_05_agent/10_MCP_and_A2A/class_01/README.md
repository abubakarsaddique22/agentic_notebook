# Class 1 — MCP Server & Client (STDIO)

## Goal
Python mein pehla MCP server create karna, MCP client se connect karna, available tools discover karna aur unhein call karna. **Is class mein LLM/LangChain nahi hai.**

## Core concepts (Roman Urdu)
- **MCP Server:** Functions aur capabilities expose karta hai jo MCP clients call kar sakte hain.
- **MCP Client:** Server se protocol ke through connect hota hai, tools discover aur call karta hai.
- **Tool:** `@server.tool()` se registered Python function; client `call_tool()` use karke run karta hai.
- **STDIO:** Client server ko local subprocess ki tarah launch karke standard input/output streams par baat karta hai. Is method mein HTTP URL/port nahi chahiye.
- **Async:** MCP client calls network/process I/O ke liye `await` use karte hain.

## Files
```text
class_01/
├── server.py
├── client.py
└── README.md
```

## Setup (Windows PowerShell; project root)
```powershell
py -m venv .venv
.venv\Scripts\activate
pip install -U "mcp[cli]"
```

## `server.py` — full code
```python
from mcp.server import MCPServer

server = MCPServer("Travel MCP Server")

@server.tool()
def search_flights(origin: str, destination: str) -> dict:
    """Return demo flight information, not live availability."""
    return {
        "airline": "Emirates",
        "origin": origin,
        "destination": destination,
        "price": 85000,
        "currency": "PKR",
        "demo": True,
    }

@server.tool()
def calculate_budget(flight_price: int, hotel_price: int) -> int:
    """Calculate flight plus hotel estimate."""
    return flight_price + hotel_price

if __name__ == "__main__":
    server.run()
```

## `client.py` — full code
```python
import asyncio
import sys
from pathlib import Path
from mcp import Client, StdioServerParameters
from mcp.types import TextContent

async def main():
    server_path = Path(__file__).parent / "server.py"
    params = StdioServerParameters(command=sys.executable, args=[str(server_path)])

    async with Client(params) as client:
        print("Connected to MCP Server!")
        tools = await client.list_tools()
        print("Available Tools:")
        for tool in tools.tools:
            print("-", tool.name)

        flights = await client.call_tool(
            "search_flights", {"origin": "Lahore", "destination": "Dubai"}
        )
        print("Flight Result:")
        for block in flights.content:
            if isinstance(block, TextContent):
                print(block.text)

        budget = await client.call_tool(
            "calculate_budget", {"flight_price": 85000, "hotel_price": 45000}
        )
        print("Budget Result:")
        for block in budget.content:
            if isinstance(block, TextContent):
                print(block.text)

if __name__ == "__main__":
    asyncio.run(main())
```

## Run
Project root se:
```powershell
cd class_01
python client.py
```
Client khud STDIO server start karega. `server.py` ko separate run karne ki need nahi.

## Expected behavior
- `search_flights` aur `calculate_budget` tools list honge.
- Flight result mein Lahore → Dubai, Emirates aur demo price 85,000 PKR aayega.
- Calculated budget **130,000 PKR** hoga.
- MCP response raw structured/text block format mein print ho sakta hai.

## Request flow
```text
client.py -> launch server.py (STDIO) -> list_tools()
          -> call_tool(search_flights) -> result
          -> call_tool(calculate_budget) -> result
```

## Practice
1. Lahore/Dubai ko kisi aur origin/destination se replace karo.
2. `calculate_budget` mein `food_price` add karo.
3. `calculate_days_cost(days, per_day_cost)` tool banao.
4. Client se new tool call karo.

## Common issues
- `ModuleNotFoundError: mcp`: virtual environment activate karo aur package install verify karo.
- Path error: `server.py` aur `client.py` same `class_01` folder mein hon.
- STDIO mein server se unnecessary `print()` mat karo, protocol messages disturb ho sakte hain.

**Next:** Class 2 mein Resources, Resource Templates aur Prompts.
