# Class 3 — MCP + LangChain AI Agent (Groq)

## Goal
Class 2 Travel MCP server ko LLM-driven LangChain agent se connect karna. Agent tools discover kare, model tool select kare, MCP server tool run kare, model final answer compose kare. MCP Resources aur Prompt ko explicitly context mein load karna.

## New concepts
- **LLM:** `ChatGroq(model="openai/gpt-oss-20b")` natural-language response aur tool calling handle karta hai.
- **MCPAdapter:** MCP server ke tools ko LangChain-compatible tools mein expose karta hai.
- **create_agent:** LangChain ka tool-using agent banata hai.
- **ainvoke:** Async agent execution start karta hai.
- **HumanMessage / AIMessage / ToolMessage:** Model input, model response/tool request, aur tool response ka trace.
- **Tool calling:** LLM tool select kar sakta hai; kitne aur kis order mein calls hongi **guaranteed nahi**.

## Folder
```text
MCP_Practical/
├── .env                     # NEVER commit secrets
└── class_03/
    ├── server.py
    ├── agent.py
    └── README.md
```

## Dependencies (project root, Windows PowerShell)
```powershell
.venv\Scripts\activate
pip install -U "mcp[cli]" "langchain[mcp]" langchain-groq python-dotenv
```

Root `.env`:
```dotenv
GROQ_API_KEY=your_actual_groq_api_key
```

## `server.py`
**Class 2 ka `server.py` copy karo**, aur `search_flights`, `travel://preferences`, `city://{city}/guide`, `plan_business_trip` ko unchanged rakho. Is extra tool ko `server.run()` se **pehle** register karo:
```python
@server.tool()
def calculate_budget(flight_price: int, hotel_price: int) -> int:
    """Return estimated flight plus hotel total."""
    return flight_price + hotel_price
```

## `agent.py` — full code
```python
import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv
from mcp import Client, StdioServerParameters
from mcp.types import TextContent, TextResourceContents
from langchain.mcp import MCPAdapter
from langchain.agents import create_agent
from langchain_groq import ChatGroq
import sys

BASE_DIR = Path(__file__).resolve().parent
SERVER_PATH = BASE_DIR / "server.py"
load_dotenv(BASE_DIR.parent / ".env")

if not os.getenv("GROQ_API_KEY"):
    raise RuntimeError("GROQ_API_KEY missing in project root .env")

llm = ChatGroq(
    model="openai/gpt-oss-20b",
    temperature=0,
    api_key=os.getenv("GROQ_API_KEY"),
)

async def load_mcp_context(destination: str, days: int):
    params = StdioServerParameters(
        command=sys.executable, args=[str(SERVER_PATH)]
    )
    async with Client(params) as client:
        pref = await client.read_resource("travel://preferences")
        preferences = "\n".join(
            x.text for x in pref.contents if isinstance(x, TextResourceContents)
        )

        city = await client.read_resource(f"city://{destination}/guide")
        city_guide = "\n".join(
            x.text for x in city.contents if isinstance(x, TextResourceContents)
        )

        prompt = await client.get_prompt(
            "plan_business_trip",
            {"destination": destination, "days": str(days)},
        )
        planning_prompt = "\n".join(
            x.content.text for x in prompt.messages
            if isinstance(x.content, TextContent)
        )
    return preferences, city_guide, planning_prompt

async def main():
    origin, destination, days = "Lahore", "Dubai", 5
    preferences, city_guide, planning_prompt = await load_mcp_context(
        destination, days
    )

    system_prompt = f"""You are a Business Travel AI Assistant.
TRAVEL PREFERENCES:
{preferences}
CITY GUIDE:
{city_guide}
PLANNING INSTRUCTIONS:
{planning_prompt}
RULES:
- Use search_flights for sample flight details.
- Use calculate_budget for the estimated flight + hotel total.
- Flight data is DEMO, not actual availability.
- Assume hotel estimate 45000 PKR total.
- Do not claim reservations have been made.
- Respond in easy Roman Urdu.
"""

    async with MCPAdapter(SERVER_PATH) as adapter:
        tools = await adapter.list_tools()
        print("DISCOVERED TOOLS:", [tool.name for tool in tools])
        agent = create_agent(model=llm, tools=tools, system_prompt=system_prompt)

        question = f"""Plan my {days}-day business trip from {origin} to {destination}.
Search a flight using the MCP tool.
Use hotel estimate 45000 PKR total and calculate combined cost
using the MCP budget tool. Give a short travel plan."""

        result = await agent.ainvoke(
            {"messages": [{"role": "user", "content": question}]}
        )

        print("\n=== MESSAGE FLOW ===")
        for msg in result["messages"]:
            print("\n", type(msg).__name__)
            if getattr(msg, "tool_calls", None):
                for call in msg.tool_calls:
                    print("TOOL:", call["name"], "ARGS:", call["args"])
            print("CONTENT:", msg.content)

        print("\n=== FINAL ANSWER ===")
        print(result["messages"][-1].content)

if __name__ == "__main__":
    asyncio.run(main())
```

## Run
```powershell
cd class_03
python agent.py
```
`server.py` ko separately run nahi karna: local STDIO adapter server launch karta hai.

## Runtime flow
```text
agent.py
  -> MCP Client: read preferences + city guide + prompt
  -> host inserts them in system_prompt
  -> MCPAdapter discovers MCP tools
  -> LangChain create_agent + Groq model
  -> LLM requests search_flights (if selected)
  -> MCP server runs tool, result returns to LLM
  -> LLM requests calculate_budget (if selected)
  -> final travel plan + message trace
```

## Expected behavior
- Discovered tools: `search_flights`, `calculate_budget`.
- Model may call `search_flights(origin='Lahore', destination='Dubai')`.
- Model may call `calculate_budget(flight_price=85000, hotel_price=45000)`; total **130000 PKR**.
- Final answer in Roman Urdu; all flight information explicitly **demo**, not real availability.

## Practical clarifications
1. **`MCPAdapter` kya karta hai?** Tool definitions ko LangChain integration deta hai; MCP Resource/Prompt content automatic system message mein nahi aata.
2. **`load_mcp_context()` kyun?** Host ko resource aur prompt manually read karke model ko provide karna hota hai.
3. **Tool result vs final answer?** Tool raw data return karta hai; LLM us data se natural language answer likhta hai.
4. **Kya tool call guaranteed?** Nahi, unless application enforce kare; prompt ki instruction alone guarantee nahi.
5. **Real deployment?** Yahan local STDIO/demo. Class 4 mein Streamable HTTP; later real weather API, RAG aur approval.

## Practice
1. `search_flights` tool call ka naam aur arguments output mein check karo.
2. Destination change karke generated arguments observe karo.
3. `calculate_daily_cost(total_budget, days)` naya MCP tool add karo.
4. Trace mein HumanMessage, AIMessage, ToolMessage identify karo.

**Next:** Class 4 — STDIO → Streamable HTTP MCP.
