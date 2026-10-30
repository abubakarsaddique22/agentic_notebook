
import asyncio
import os
from dotenv import load_dotenv

from mcp import Client
from langchain.mcp import MCPAdapter
from langchain.agents import create_agent
from langchain_groq import ChatGroq

load_dotenv()

URL = "http://127.0.0.1:8001/mcp"

# 1. LLM setup
llm = ChatGroq(
    model="openai/gpt-oss-20b",
    temperature=0,
    api_key=os.getenv("Groq_API_KEY")
)


# 2. MCP Resources + Prompt
async def get_context():
    async with Client(URL) as client:

        preferences = await client.read_resource(
            "travel://preferences"
        )

        guide = await client.read_resource(
            "city://Dubai/guide"
        )

        prompt = await client.get_prompt(
            "plan_business_trip",
            {"destination": "Dubai", "days": "5"}
        )

        return preferences, guide, prompt


# 3. Main function
async def main():

    # Get MCP context
    preferences, guide, prompt = await get_context()

    # System instructions
    instructions = f"""
    You are a Travel AI Assistant.
    Reply in Roman Urdu.

    User Preferences:
    {preferences}

    Dubai Guide:
    {guide}

    Trip Planning Prompt:
    {prompt}

    Use MCP tools for weather, flights and budget.
    Never invent current weather.
    Flights are demo data, not real tickets.
    Hotel budget is PKR 45000.
    Never claim a booking is confirmed.
    """

    # Connect MCP Server
    config = {
        "mcpServers": {
            "travel": {"url": URL}
        }
    }

    async with MCPAdapter(config) as adapter:

        # Get MCP Tools
        tools = await adapter.list_tools()

        print("Available Tools:", [tool.name for tool in tools])

        # Create LangChain Agent
        agent = create_agent(
            model=llm,
            tools=tools,
            system_prompt=instructions
        )

        # Ask question
        response = await agent.ainvoke({
            "messages": [{
                "role": "user",
                "content": """
                Plan my 5-day Lahore to Dubai trip.
                Check current Dubai weather and its timestamp.
                Search demo flights.
                Calculate flight + PKR 45000 hotel budget.
                """
            }]
        })

        print("\nFINAL ANSWER:")
        print(response["messages"][-1].content)


asyncio.run(main())
