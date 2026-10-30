# Class 2 — MCP Resources, Resource Templates & Prompts

## Goal
Class 1 ke MCP server ko expand karna: tools ke ilawa fixed context, dynamic context aur reusable prompts expose karna; client se teeno retrieve karna. **Abhi LLM nahi use ho raha.**

## Concepts
| Primitive | Roman Urdu matlab | Example | Client method |
|---|---|---|---|
| Tool | **DO:** code/function execute karo | `search_flights` | `call_tool()` |
| Resource | **KNOW:** given URI par context read karo | `travel://preferences` | `read_resource()` |
| Resource Template | **Dynamic KNOW:** URI ka parameter vary karo | `city://{city}/guide` | `read_resource("city://Dubai/guide")` |
| Prompt | **GUIDE:** reusable instruction template | `plan_business_trip` | `get_prompt()` |

**Yaad rakho:** Resources aur Prompts khud automatically LLM ko nahi milte. MCP host/client unhein load karke LLM context mein add karta hai (Class 3).

## Folder
```text
class_02/
├── server.py
├── client.py
└── README.md
```

## Setup
Class 1 ka active virtual environment reuse karo:
```powershell
.venv\Scripts\activate
pip install -U "mcp[cli]"
```

## `server.py` — full code
```python
from mcp.server import MCPServer

server = MCPServer("Travel MCP Server")

@server.tool()
def search_flights(origin: str, destination: str) -> dict:
    """Return example flight, not real availability."""
    return {
        "airline": "Emirates", "origin": origin,
        "destination": destination, "price": 85000,
        "currency": "PKR", "demo": True,
    }

@server.resource("travel://preferences")
def travel_preferences() -> str:
    """Fixed travel context."""
    return """Preferred airline: Emirates
Preferred seat: Window
Preferred flight class: Economy
Preferred hotel: 4-star
Travel budget: 200000 PKR"""

@server.resource("city://{city}/guide")
def city_guide(city: str) -> str:
    """Dynamic city-specific generic guide."""
    return f"""City: {city}
Recommended hotel: Near business center
Transport: Use airport taxi
Important: Check weather and local rules"""

@server.prompt()
def plan_business_trip(destination: str, days: str) -> str:
    """Reusable planning instructions."""
    return f"""Plan a {days}-day business trip to {destination}.
1. Check travel preferences.
2. Read the destination city guide.
3. Search suitable flights.
4. Recommend a hotel category.
5. Estimate the travel budget.
6. Provide a final itinerary."""

if __name__ == "__main__":
    server.run()
```

## `client.py` — full code
```python
import asyncio
import sys
from pathlib import Path
from mcp import Client, StdioServerParameters
from mcp.types import TextContent, TextResourceContents

async def main():
    params = StdioServerParameters(
        command=sys.executable,
        args=[str(Path(__file__).parent / "server.py")],
    )
    async with Client(params) as client:
        print("TOOLS")
        for item in (await client.list_tools()).tools:
            print("-", item.name)

        print("FIXED RESOURCES")
        for item in (await client.list_resources()).resources:
            print("-", item.uri)

        print("TRAVEL PREFERENCES")
        result = await client.read_resource("travel://preferences")
        for item in result.contents:
            if isinstance(item, TextResourceContents):
                print(item.text)

        print("RESOURCE TEMPLATES")
        for item in (await client.list_resource_templates()).resource_templates:
            print("-", item.uri_template)

        print("CITY GUIDE")
        city_result = await client.read_resource("city://Dubai/guide")
        for item in city_result.contents:
            if isinstance(item, TextResourceContents):
                print(item.text)

        print("PROMPTS")
        for item in (await client.list_prompts()).prompts:
            print("-", item.name)

        print("PLANNING PROMPT")
        prompt = await client.get_prompt(
            "plan_business_trip", {"destination": "Dubai", "days": "5"}
        )
        for msg in prompt.messages:
            if isinstance(msg.content, TextContent):
                print(msg.content.text)

        print("FLIGHT TOOL RESULT")
        flight = await client.call_tool(
            "search_flights", {"origin": "Lahore", "destination": "Dubai"}
        )
        for item in flight.content:
            if isinstance(item, TextContent):
                print(item.text)

if __name__ == "__main__":
    asyncio.run(main())
```

## Run
```powershell
cd class_02
python client.py
```

## Expected behavior
- Tool `search_flights` listed.
- Fixed resource `travel://preferences` listed aur read hogi.
- Template `city://{city}/guide` listed aur `city://Dubai/guide` read hoga.
- Prompt `plan_business_trip` listed aur Dubai/5-days instruction milegi.
- Demo flight result show hoga.

## Questions jo clear hone chahiye
- **Resource vs Tool?** Context read vs executable action. Resources dynamically generated bhi ho sakte hain.
- **Resource Template vs Resource?** Template URI mein placeholders hote hain, e.g. `{city}`.
- **Prompt vs system prompt?** MCP prompt reusable server-provided message template hai; host choose karta hai kaise model ko use karwana hai.

## Practice
1. `company://policy` fixed resource add karo.
2. `city://Lahore/guide` read karo.
3. `plan_business_trip` mein `budget` parameter add karo.
4. Client se new resource/prompt retrieve karke print karo.

**Next:** Class 3 mein LLM + LangChain Agent MCP tools ko automatically call karega.
