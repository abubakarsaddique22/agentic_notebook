import asyncio
import sys
from pathlib import Path

from mcp import Client, StdioServerParameters
from mcp.types import TextContent


async def main():

    # MCP Server ka path
    server_path = Path(__file__).parent / "server.py"

    # STDIO connection settings
    params = StdioServerParameters(
        command=sys.executable,
        args=[str(server_path)]
    )

    # Connect to MCP Server
    async with Client(params) as client:

        print("Connected to MCP Server!")

        # Discover tools
        tools = await client.list_tools()

        print("\nAvailable Tools:")
        for tool in tools.tools:
            print("-", tool.name)

        # Call first tool
        result = await client.call_tool(
            "search_flights",
            {
                "origin": "Karachi",
                "destination": "Istanbul"
            }
        )

        print("\nFlight Result:")

        for block in result.content:
            if isinstance(block, TextContent):
                print(block.text)

        # Call second tool
        budget = await client.call_tool(
            "calculate_budget",
            {
                "flight_price": 85000,
                "hotel_price": 45000,
                "food_price":10000,
            }
        )

        print("\nBudget Result:")

        for block in budget.content:
            if isinstance(block, TextContent):
                print(block.text)


if __name__ == "__main__":
    asyncio.run(main())
