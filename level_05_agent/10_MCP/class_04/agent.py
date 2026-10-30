
import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv
from mcp import Client
from mcp.types import TextContent, TextResourceContents

from langchain.mcp import MCPAdapter
from langchain.agents import create_agent
from langchain_groq import ChatGroq


# =============================================
# 1. CONFIG
# =============================================

BASE_DIR = Path(__file__).resolve().parent
load_dotenv()

MCP_URL = "http://127.0.0.1:8001/mcp"

if not os.getenv("Groq_API_KEY"):
    raise RuntimeError("Groq_API_KEY missing")


# =============================================
# 2. LLM
# =============================================

llm = ChatGroq(
    model="openai/gpt-oss-20b",
    temperature=0,
    api_key=os.getenv("Groq_API_KEY")
)


# =============================================
# 3. LOAD MCP CONTEXT OVER HTTP
# =============================================

async def load_mcp_context(destination, days):

    async with Client(MCP_URL) as client:

        # Fixed Resource
        pref_result = await client.read_resource(
            "travel://preferences"
        )

        preferences = "\n".join(
            item.text
            for item in pref_result.contents
            if isinstance(item, TextResourceContents)
        )

        # Dynamic Resource
        city_result = await client.read_resource(
            f"city://{destination}/guide"
        )

        city_guide = "\n".join(
            item.text
            for item in city_result.contents
            if isinstance(item, TextResourceContents)
        )

        # MCP Prompt
        prompt_result = await client.get_prompt(
            "plan_business_trip",
            {
                "destination": destination,
                "days": str(days)
            }
        )

        planning_prompt = "\n".join(
            message.content.text
            for message in prompt_result.messages
            if isinstance(message.content, TextContent)
        )

    return preferences, city_guide, planning_prompt


# =============================================
# 4. MAIN AI APPLICATION
# =============================================

async def main():

    origin = "Lahore"
    destination = "Dubai"
    days = 5

    # -----------------------------------------
    # Load MCP resources
    # -----------------------------------------

    print("Reading MCP context over HTTP...")

    preferences, city_guide, planning_prompt = (
        await load_mcp_context(destination, days)
    )

    # -----------------------------------------
    # Agent instructions
    # -----------------------------------------

    system_prompt = f"""
You are a business travel AI assistant.

TRAVEL PREFERENCES:
{preferences}

DESTINATION CONTEXT:
{city_guide}

MCP PLANNING PROMPT:
{planning_prompt}

Rules:
- Use search_flights for flight information.
- Use calculate_budget for total estimation.
- Hotel estimate is 45000 PKR total.
- Flight information is sample/demo data.
- Do not claim a booking or live availability.
- Answer in simple Roman Urdu.
"""

    # -----------------------------------------
    # MCPAdapter connects via HTTP URL
    # -----------------------------------------

    config = {
        "mcpServers": {
            "travel": {
                "url": MCP_URL
            }
        }
    }

    async with MCPAdapter(config) as adapter:

        # Discover HTTP MCP tools
        tools = await adapter.list_tools()

        print("\nDISCOVERED TOOLS:")

        for tool in tools:
            print("-", tool.name)

        # Create LangChain Agent
        agent = create_agent(
            model=llm,
            tools=tools,
            system_prompt=system_prompt
        )

        user_question = f"""
Plan a {days}-day business trip
from {origin} to {destination}.

Search a flight using MCP.
Hotel estimate: 45000 PKR total.

Calculate flight + hotel cost
using the MCP budget tool.

Give me a practical travel plan.
"""

        print("\nAGENT STARTED")

        # Execute agent
        result = await agent.ainvoke({
            "messages": [
                {
                    "role": "user",
                    "content": user_question
                }
            ]
        })

        # -----------------------------------------
        # Inspect agent messages
        # -----------------------------------------

        print("\n========== MESSAGE FLOW ==========")

        for message in result["messages"]:

            print("\n", type(message).__name__)

            if getattr(message, "tool_calls", None):
                for call in message.tool_calls:
                    print("TOOL:", call["name"])
                    print("ARGS:", call["args"])

            print("CONTENT:", message.content)

        # -----------------------------------------
        # Final response
        # -----------------------------------------

        print("\n========== FINAL ANSWER ==========")
        print(result["messages"][-1].content)


if __name__ == "__main__":
    asyncio.run(main())
