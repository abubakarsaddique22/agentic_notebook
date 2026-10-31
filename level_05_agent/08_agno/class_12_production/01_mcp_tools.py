"""
=====================================================================
 CLASS 12 | FILE 01: mcp_tools.py
=====================================================================
 CONCEPT: MCP Tools (kisi bhi MCP server ke tools agent ko dena)
 Kya hai : MCPTools ek toolkit hai jo MCP server se connect hota hai,
           uske tools list karta hai aur agent ko de deta hai.
           Aap ko tool ka code likhne ki zaroorat nahi.
   Local server  -> server_params=StdioServerParameters(command, args)
   Remote server -> MCPTools(url="https://.../mcp", transport="streamable-http")
 Zaroori : MCPTools ASYNC hai -> "async with" ke andar use karo,
           aur agent.arun / aprint_response (await) se chalao.
           async with -> connection khud khulta aur band hota hai.

 Run:
     uv run python class_12_production/01_mcp_tools.py
=====================================================================
"""

import asyncio
import sys
from pathlib import Path

from mcp import StdioServerParameters

from agno.agent import Agent
from agno.tools.mcp import MCPTools

from llm_setup import get_model

SERVER_FILE = Path(__file__).parent / "store_mcp_server.py"


async def main():
    server = StdioServerParameters(command=sys.executable, args=[str(SERVER_FILE)])

    async with MCPTools(server_params=server) as store_tools:
        print("MCP tools mile:", list(store_tools.functions.keys()))

        agent = Agent(
            name="mcp_support_agent",
            model=get_model(),
            tools=[store_tools],
            instructions=["Always use the store tools for orders and categories"],
            markdown=True,
        )
        await agent.aprint_response("Where is my order 1002? And which categories do you have?", stream=True)


if __name__ == "__main__":
    asyncio.run(main())
