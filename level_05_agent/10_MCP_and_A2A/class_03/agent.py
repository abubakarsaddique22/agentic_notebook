# import asyncio
# import sys
# import os
# from pathlib import Path

# from dotenv import load_dotenv

# from mcp import Client, StdioServerParameters
# from mcp.types import TextContent, TextResourceContents

# from langchain.mcp import MCPAdapter
# from langchain.agents import create_agent
# from langchain_groq import ChatGroq


# # ==================================================
# # 1. CONFIGURATION
# # ==================================================

# BASE_DIR = Path(__file__).resolve().parent
# SERVER_PATH = BASE_DIR / "server.py"

# load_dotenv()

# if not os.getenv("Groq_API_KEY"):
#     raise RuntimeError("Groq_API_KEY missing in .env")


# # ==================================================
# # 2. LLM
# # ==================================================

# llm = ChatGroq(
#     model="openai/gpt-oss-20b",
#     temperature=0,
#     api_key=os.getenv("Groq_API_KEY")
# )


# # ==================================================
# # 3. READ MCP RESOURCES + PROMPT
# # ==================================================

# async def load_mcp_context(destination, days):

#     params = StdioServerParameters(
#         command=sys.executable,
#         args=[str(SERVER_PATH)],
#         cwd=str(BASE_DIR),
#         env=os.environ.copy(),
# )

#     async with Client(params) as client:

#         # Fixed Resource
#         preferences_result = await client.read_resource(
#             "travel://preferences"
#         )

#         preferences = "\n".join(
#             item.text
#             for item in preferences_result.contents
#             if isinstance(item, TextResourceContents)
#         )

#         # Dynamic Resource
#         city_result = await client.read_resource(
#             f"city://{destination}/guide"
#         )

#         city_guide = "\n".join(
#             item.text
#             for item in city_result.contents
#             if isinstance(item, TextResourceContents)
#         )

#         # MCP Prompt
#         prompt_result = await client.get_prompt(
#             "plan_business_trip",
#             {
#                 "destination": destination,
#                 "days": str(days)
#             }
#         )

#         planning_prompt = "\n".join(
#             message.content.text
#             for message in prompt_result.messages
#             if isinstance(message.content, TextContent)
#         )

#     return preferences, city_guide, planning_prompt


# # ==================================================
# # 4. MAIN AI AGENT
# # ==================================================

# async def main():

#     origin = "Lahore"
#     destination = "Dubai"
#     days = 5

#     print("Loading MCP resources and prompt...")

#     preferences, city_guide, planning_prompt = (
#         await load_mcp_context(destination, days)
#     )

#     # Host combines MCP context with agent instructions
#     system_prompt = f"""
# You are a professional Business Travel AI Assistant.

# TRAVELER PREFERENCES:
# {preferences}

# DESTINATION GUIDE:
# {city_guide}

# MCP PLANNING INSTRUCTIONS:
# {planning_prompt}

# IMPORTANT RULES:
# - Use search_flights when flight information is needed.
# - Use calculate_budget for the total flight + hotel cost.
# - Flight results are demo data, not live availability.
# - Never claim that a booking has been made.
# - Hotel estimate: 45000 PKR total.
# - Clearly label estimated costs.
# - Respond in easy Roman Urdu.
# """

#     print("\nConnecting LangChain to MCP Server...")

#     # MCPAdapter discovers and converts MCP tools
#     async with MCPAdapter(SERVER_PATH) as adapter:

#         tools = await adapter.list_tools()

#         print("\nDISCOVERED MCP TOOLS:")
#         for tool in tools:
#             print("-", tool.name)

#         # Create LangChain Agent
#         agent = create_agent(
#             model=llm,
#             tools=tools,
#             system_prompt=system_prompt
#         )

#         # Natural-language user request
#         user_question = f"""
# Plan my {days}-day business trip
# from {origin} to {destination}.

# Search a suitable flight using the MCP tool.

# Use a hotel estimate of 45000 PKR total
# and calculate the combined flight + hotel cost
# using the MCP budget tool.

# Give a short final travel plan.
# """

#         print("\nUSER QUESTION:")
#         print(user_question)

#         # Agent execution
#         result = await agent.ainvoke({
#             "messages": [
#                 {
#                     "role": "user",
#                     "content": user_question
#                 }
#             ]
#         })

#         # Display complete message flow
#         print("\n========== AGENT MESSAGE FLOW ==========")

#         for message in result["messages"]:

#             print(f"\n{type(message).__name__}")

#             if getattr(message, "tool_calls", None):
#                 for call in message.tool_calls:
#                     print("TOOL CALL:", call["name"])
#                     print("ARGUMENTS:", call["args"])

#             print("CONTENT:", message.content)

#         # Final AI response
#         print("\n========== FINAL AI ANSWER ==========")
#         print(result["messages"][-1].content)


# if __name__ == "__main__":
#     asyncio.run(main())



import asyncio
import sys
import os
from pathlib import Path

from dotenv import load_dotenv

from mcp import Client, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import TextContent, TextResourceContents

from langchain.mcp import MCPAdapter
from langchain.agents import create_agent
from langchain_groq import ChatGroq


# ==================================================
# 1. CONFIGURATION
# ==================================================

BASE_DIR = Path(__file__).resolve().parent
SERVER_PATH = BASE_DIR / "server.py"
LOG_PATH = BASE_DIR / "mcp_server_error.log"

load_dotenv(BASE_DIR / ".env")
load_dotenv()

GROQ_API_KEY = (
    os.getenv("GROQ_API_KEY")
    or os.getenv("Groq_API_KEY")
)

if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY missing in .env")

if not SERVER_PATH.is_file():
    raise FileNotFoundError(
        f"MCP server not found: {SERVER_PATH}"
    )

print("Python:", sys.executable)
print("Server:", SERVER_PATH)
print("Server exists:", SERVER_PATH.exists())


# ==================================================
# 2. LLM
# ==================================================

llm = ChatGroq(
    model="openai/gpt-oss-20b",
    temperature=0,
    api_key=GROQ_API_KEY,
)


# ==================================================
# 3. MCP SERVER PARAMETERS
# ==================================================

params = StdioServerParameters(
    command=sys.executable,
    args=["-u", str(SERVER_PATH)],
    cwd=str(BASE_DIR),
    env=os.environ.copy(),
)


# ==================================================
# 4. READ MCP RESOURCES + PROMPT
# ==================================================

async def load_mcp_context(destination, days):

    print("\nConnecting to MCP Server...")

    # Capture server stderr for debugging
    with open(LOG_PATH, "w", encoding="utf-8") as log:

        try:
            async with Client(
                stdio_client(params, errlog=log)
            ) as client:

                print("MCP Connected Successfully!")

                # Check available tools
                tools_result = await client.list_tools()

                print("\nAvailable MCP Tools:")
                for tool in tools_result.tools:
                    print("-", tool.name)

                # ----------------------------------
                # Fixed Resource
                # ----------------------------------

                print("\nReading traveler preferences...")

                preferences_result = (
                    await client.read_resource(
                        "travel://preferences"
                    )
                )

                preferences = "\n".join(
                    item.text
                    for item in preferences_result.contents
                    if isinstance(
                        item, TextResourceContents
                    )
                )

                # ----------------------------------
                # Dynamic Resource
                # ----------------------------------

                print("Reading destination guide...")

                city_result = (
                    await client.read_resource(
                        f"city://{destination}/guide"
                    )
                )

                city_guide = "\n".join(
                    item.text
                    for item in city_result.contents
                    if isinstance(
                        item, TextResourceContents
                    )
                )

                # ----------------------------------
                # MCP Prompt
                # ----------------------------------

                print("Loading MCP planning prompt...")

                prompt_result = await client.get_prompt(
                    "plan_business_trip",
                    {
                        "destination": destination,
                        "days": str(days),
                    },
                )

                planning_prompt = "\n".join(
                    message.content.text
                    for message in prompt_result.messages
                    if isinstance(
                        message.content, TextContent
                    )
                )

                print("MCP Context Loaded Successfully!")

                return (
                    preferences,
                    city_guide,
                    planning_prompt,
                )

        except Exception as error:

            print("\nMCP CONNECTION ERROR!")
            print("Error:", repr(error))
            print("Server error log:", LOG_PATH)

            log.flush()

            raise


# ==================================================
# 5. MAIN AI AGENT
# ==================================================

async def main():

    origin = "Lahore"
    destination = "Dubai"
    days = 5

    print("\nLoading MCP resources and prompt...")

    preferences, city_guide, planning_prompt = (
        await load_mcp_context(destination, days)
    )

    # ----------------------------------
    # System Prompt
    # ----------------------------------

    system_prompt = f"""
You are a professional Business Travel AI Assistant.

TRAVELER PREFERENCES:
{preferences}

DESTINATION GUIDE:
{city_guide}

MCP PLANNING INSTRUCTIONS:
{planning_prompt}

IMPORTANT RULES:
- Use search_flights when flight information is needed.
- Use calculate_budget for total flight + hotel cost.
- Flight results are demo data, not live availability.
- Never claim that a booking has been made.
- Hotel estimate: 45000 PKR total.
- Clearly label estimated costs.
- Respond in easy Roman Urdu.
"""

    print("\nConnecting LangChain to MCP Server...")

    # ----------------------------------
    # MCP Tools + LangChain
    # ----------------------------------

    async with MCPAdapter(SERVER_PATH) as adapter:

        tools = await adapter.list_tools()

        print("\nDISCOVERED MCP TOOLS:")

        for tool in tools:
            print("-", tool.name)

        # Create LangChain AI Agent
        agent = create_agent(
            model=llm,
            tools=tools,
            system_prompt=system_prompt,
        )

        # ----------------------------------
        # User Question
        # ----------------------------------

        user_question = f"""
Plan my {days}-day business trip
from {origin} to {destination}.

Search a suitable flight using the MCP tool.

Use a hotel estimate of 45000 PKR total
and calculate the combined flight + hotel cost
using the MCP budget tool.

Give a short final travel plan.
"""

        print("\nUSER QUESTION:")
        print(user_question)

        # ----------------------------------
        # Agent Execution
        # ----------------------------------

        result = await agent.ainvoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": user_question,
                    }
                ]
            }
        )

        # ----------------------------------
        # Message Flow
        # ----------------------------------

        print("\n========== AGENT MESSAGE FLOW ==========")

        for message in result["messages"]:

            print(f"\n{type(message).__name__}")

            if getattr(message, "tool_calls", None):

                for call in message.tool_calls:
                    print("TOOL CALL:", call["name"])
                    print("ARGUMENTS:", call["args"])

            print("CONTENT:", message.content)

        # ----------------------------------
        # Final Answer
        # ----------------------------------

        print("\n========== FINAL AI ANSWER ==========")
        print(result["messages"][-1].content)


# ==================================================
# 6. RUN APPLICATION
# ==================================================

if __name__ == "__main__":

    try:
        asyncio.run(main())

    except Exception as error:

        print("\nAPPLICATION FAILED")
        print("Error:", repr(error))

        if LOG_PATH.exists():

            print("\n========== MCP SERVER LOG ==========")

            log_content = LOG_PATH.read_text(
                encoding="utf-8",
                errors="replace",
            )

            print(
                log_content
                if log_content.strip()
                else "No server stderr captured."
            )
