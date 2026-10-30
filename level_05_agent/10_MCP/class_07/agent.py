
import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv

from mcp import Client
from langchain.mcp import MCPAdapter
from langchain.agents import create_agent
from langchain_groq import ChatGroq

# 1. Environment
ROOT = Path(__file__).resolve().parent
load_dotenv()

# 2. MCP Server URLs
URLS = {
    "travel": "http://127.0.0.1:8001/mcp",
    "policy": "http://127.0.0.1:8002/mcp",
    "work": "http://127.0.0.1:8003/mcp"
}

# 3. Groq Model
llm = ChatGroq(
    model="openai/gpt-oss-20b",
    temperature=0,
    api_key=os.getenv("Groq_API_KEY")
)


# 4. Get MCP Resources and Prompt
async def get_context():

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

    async with Client(URLS["policy"]) as client:

        policy = await client.read_resource(
            "policy://travel-summary"
        )

    # Extract actual text
    preferences_text = "\n".join(
        item.text for item in preferences.contents
        if hasattr(item, "text")
    )

    guide_text = "\n".join(
        item.text for item in guide.contents
        if hasattr(item, "text")
    )

    prompt_text = "\n".join(
        message.content.text for message in prompt.messages
        if hasattr(message.content, "text")
    )

    policy_text = "\n".join(
        item.text for item in policy.contents
        if hasattr(item, "text")
    )

    return preferences_text, guide_text, prompt_text, policy_text


# 5. Main Function
async def main():

    preferences, guide, prompt, policy = await get_context()

    # Agent Instructions
    instructions = f"""
    You are a Business Travel AI Assistant.
    Reply in easy Roman Urdu.

    Traveler Preferences:
    {preferences}

    Dubai Guide:
    {guide}

    MCP Planning Prompt:
    {prompt}

    Company Policy Document:
    {policy}

    Rules:
    - Use travel_get_live_weather for current weather.
    - If weather fails, explain that data is unavailable.
    - Use travel_search_flights for demo flights.
    - Use policy_search_company_policy for semantic RAG search.
    - Check economy, hotel and reimbursement policies.
    - Cite retrieved chunk_id and source for policy claims.
    - If semantic retrieval fails, report the failure.
    - Use travel_calculate_budget for flight + 45000 PKR hotel.
    - Create exactly ONE demo task using work_create_trip_task.
    - Do not directly compare INR and PKR.
    - Never claim any real booking has happened.
    - Give a concise final answer.
    """

    # 6. Configure MCP Servers
    config = {
        "mcpServers": {
            "travel": {"url": URLS["travel"]},
            "policy": {"url": URLS["policy"]},
            "work": {"url": URLS["work"]}
        }
    }

    # 7. Connect MCP Servers
    async with MCPAdapter(config) as adapter:

        tools = await adapter.list_tools()

        print("Available Tools:")
        print([tool.name for tool in tools])

        # 8. Create Agent
        agent = create_agent(
            model=llm,
            tools=tools,
            system_prompt=instructions
        )

        # 9. User Question
        question = """
        Plan my 5-day Lahore to Dubai business trip.

        1. Check Dubai weather and observation time.
        2. Search sample flights.
        3. Use semantic RAG to check company policies.
        4. Check economy, hotel and reimbursement rules.
        5. Calculate flight + 45000 PKR hotel budget.
        6. Create one demo task:
           Prepare Dubai meeting agenda.

        Cite policy chunk IDs and sources.
        Clearly mention all demo data.
        """

        # 10. Run Agent
        response = await agent.ainvoke({
            "messages": [
                {"role": "user", "content": question}
            ]
        })

        # 11. Show Tool Calls
        print("\nTOOL CALLS:")

        for message in response["messages"]:
            for call in getattr(message, "tool_calls", []) or []:
                print("Tool:", call["name"])
                print("Arguments:", call["args"])

        # 12. Final Answer
        print("\nFINAL ANSWER:")
        print(response["messages"][-1].content)


if __name__ == "__main__":
    asyncio.run(main())
