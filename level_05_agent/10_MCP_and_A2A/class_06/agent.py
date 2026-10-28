
import asyncio
import os
from dotenv import load_dotenv

from mcp import Client
from langchain.mcp import MCPAdapter
from langchain.agents import create_agent
from langchain_groq import ChatGroq

load_dotenv()

# 1. MCP Server URLs
URLS = {
    "travel": "http://127.0.0.1:8001/mcp",
    "policy": "http://127.0.0.1:8002/mcp",
    "work": "http://127.0.0.1:8003/mcp"
}

# 2. Groq LLM
llm = ChatGroq(
    model="openai/gpt-oss-20b",
    temperature=0,
    api_key=os.getenv("GROQ_API_KEY")
)


# 3. Load MCP Resources and Prompt
async def get_context():

    # Travel MCP Server
    async with Client(URLS["travel"]) as client:

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

    # Policy MCP Server
    async with Client(URLS["policy"]) as client:

        policy = await client.read_resource(
            "policy://travel-summary"
        )

    return preferences, guide, prompt, policy


# 4. Main Function
async def main():

    # Get MCP Context
    preferences, guide, prompt, policy = await get_context()

    # System Prompt
    instructions = f"""
    You are a Business Travel AI Assistant.
    Reply in simple Roman Urdu.

    Traveler Preferences:
    {preferences}

    City Guide:
    {guide}

    Trip Planning Prompt:
    {prompt}

    Company Policies:
    {policy}

    Rules:
    - Check real weather using travel_get_live_weather.
    - Search demo flights using travel_search_flights.
    - Check policies using policy_search_company_policy.
    - Calculate flight + 45000 PKR hotel budget.
    - Create exactly one demo task using work_create_trip_task.
    - Do not compare INR and PKR directly.
    - Never claim demo flights or bookings are real.
    - If weather is unavailable, explain it.
    """

    # 5. Configure Multiple MCP Servers
    config = {
        "mcpServers": {
            "travel": {"url": URLS["travel"]},
            "policy": {"url": URLS["policy"]},
            "work": {"url": URLS["work"]}
        }
    }

    # 6. Connect All MCP Servers
    async with MCPAdapter(config) as adapter:

        tools = await adapter.list_tools()

        print("Available Tools:")
        print([tool.name for tool in tools])

        # 7. Create AI Agent
        agent = create_agent(
            model=llm,
            tools=tools,
            system_prompt=instructions
        )

        # 8. User Question
        question = """
        Plan my 5-day Lahore to Dubai business trip.

        1. Check current Dubai weather and observation time.
        2. Search sample flights.
        3. Check company flight and hotel policies.
        4. Calculate flight + 45000 PKR hotel budget.
        5. Create one demo task:
           Prepare Dubai meeting agenda.

        Clearly mention all demo data.
        """

        # 9. Run Agent
        response = await agent.ainvoke({
            "messages": [
                {"role": "user", "content": question}
            ]
        })

        # 10. Final Answer
        print("\nFINAL ANSWER:")
        print(response["messages"][-1].content)


if __name__ == "__main__":
    asyncio.run(main())
