"""EASY VERSION: Ek agent jo 3 MCP servers (travel, policy, work) ke tools use karta hai."""
import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv
from mcp import Client
from mcp.types import TextContent, TextResourceContents
from langchain.mcp import MCPAdapter
from langchain.agents import create_agent
from langchain_groq import ChatGroq


# ============================================
# 1. SETTINGS
# ============================================

ROOT = Path(__file__).resolve().parent
load_dotenv()

# Teen servers, teen ports (har server alag terminal mein chalna chahiye)
TRAVEL_URL = "http://127.0.0.1:8001/mcp"
POLICY_URL = "http://127.0.0.1:8002/mcp"
WORK_URL = "http://127.0.0.1:8003/mcp"
# Booking server (8004) jaan boojh kar yahan NAHI hai: agent khud booking na kar sake.


# ============================================
# 2. HELPER FUNCTIONS
# ============================================

def resource_to_text(result) -> str:
    """Resource ke andar se sirf text nikalta hai."""
    texts = []
    for item in result.contents:
        if isinstance(item, TextResourceContents):
            texts.append(item.text)
    return "\n".join(texts)


def prompt_to_text(result) -> str:
    """Prompt ke messages se sirf text nikalta hai."""
    texts = []
    for message in result.messages:
        if isinstance(message.content, TextContent):
            texts.append(message.content.text)
    return "\n".join(texts)


# ============================================
# 3. SERVERS SE CONTEXT LAO (resources + prompt)
# ============================================

async def load_context():

    # Travel server se: preferences, city guide, planning prompt
    async with Client(TRAVEL_URL) as client:
        preferences = resource_to_text(await client.read_resource("travel://preferences"))
        city_guide = resource_to_text(await client.read_resource("city://Dubai/guide"))

        prompt_result = await client.get_prompt(
            "plan_business_trip",
            {"destination": "Dubai", "days": "5"},
        )
        planning_prompt = prompt_to_text(prompt_result)

    # Policy server se: company policy ka summary
    async with Client(POLICY_URL) as client:
        policy = resource_to_text(await client.read_resource("policy://travel-summary"))

    return preferences, city_guide, planning_prompt, policy


# ============================================
# 4. MAIN
# ============================================

async def main():

    if not os.getenv("GROQ_API_KEY"):
        raise RuntimeError("GROQ_API_KEY missing in MCP_Practical/.env")

    # ---------- Step 1: context lao ----------
    preferences, city_guide, planning_prompt, policy = await load_context()

    # ---------- Step 2: agent ke liye instructions ----------
    system_prompt = f"""You are a business trip assistant. Reply in easy Roman Urdu.

Traveler preferences (demo):
{preferences}

City guide (illustrative):
{city_guide}

MCP planning prompt:
{planning_prompt}

Demo company policies:
{policy}

Rules:
- travel_get_live_weather: current weather lao. Fail ho to saaf batao.
- travel_search_flights: SAMPLE flight data (asli seats nahi).
- policy_search_company_policy: company rules dhoondo (RAG). Final answer mein chunk_id aur source likho. Fail ho to batao.
- travel_calculate_budget: sample flight price + hotel estimate (45000 PKR total) jodo.
- work_create_trip_task: sirf EK demo task banao, kyunki user ne manga hai.
- Policy mein hotel 12000 INR/night hai. Currency alag hai, PKR se seedha compare mat karo.
- Kabhi ye mat kaho ke asli booking, asli task ya asli flight reservation hui hai.
- Booking tools tumhare paas nahi hain. Booking sirf recommend kar sakte ho.
- Final answer chhota rakho."""

    # ---------- Step 3: teeno servers se tools lo ----------
    config = {
        "mcpServers": {
            "travel": {"url": TRAVEL_URL},
            "policy": {"url": POLICY_URL},
            "work": {"url": WORK_URL},
        }
    }
    # Tool ke naam ke aage server ka naam lag jata hai:
    # search_flights -> travel_search_flights

    async with MCPAdapter(config) as adapter:
        tools = await adapter.list_tools()
        print("DISCOVERED TOOLS:", [tool.name for tool in tools])

        # ---------- Step 4: agent banao ----------
        llm = ChatGroq(model="openai/gpt-oss-20b", temperature=0)
        agent = create_agent(model=llm, tools=tools, system_prompt=system_prompt)

        # ---------- Step 5: sawal poocho ----------
        question = (
            "Plan a 5-day business trip Lahore to Dubai. "
            "Check live Dubai weather, find a sample flight, "
            "use semantic policy search to check economy, hotel and reimbursement rules, "
            "calculate combined demo flight and 45000 PKR hotel estimate, "
            "and create one demo preparation task titled Prepare Dubai meeting agenda. "
            "Clearly label sample data and current weather observation time."
        )

        result = await agent.ainvoke({"messages": [{"role": "user", "content": question}]})

        # ---------- Step 6: dekho agent ne kya kya kiya ----------
        print("\nMESSAGE FLOW:")
        for message in result["messages"]:
            print("\n", type(message).__name__)

            tool_calls = getattr(message, "tool_calls", None) or []
            for call in tool_calls:
                print("TOOL:", call["name"], "ARGS:", call["args"])

            print("CONTENT:", message.content)

        print("\nFINAL ANSWER:\n", result["messages"][-1].content)
        print("\nSECURITY: Booking service is excluded from autonomous agent tools.")


if __name__ == "__main__":
    asyncio.run(main())