
import asyncio

from mcp import Client
from mcp.types import TextContent, TextResourceContents


MCP_URL = "http://127.0.0.1:8001/mcp"


async def main():

    # Connect to running HTTP MCP server
    async with Client(MCP_URL) as client:

        print("CONNECTED TO HTTP MCP SERVER")

        print("Server:", client.server_info)

        # ----------------------------------------
        # 1. DISCOVER TOOLS
        # ----------------------------------------

        tools = await client.list_tools()

        print("\nAVAILABLE TOOLS")

        for tool in tools.tools:
            print("-", tool.name)

        # ----------------------------------------
        # 2. CALL FLIGHT TOOL
        # ----------------------------------------

        result = await client.call_tool(
            "search_flights",
            {
                "origin": "Lahore",
                "destination": "Dubai"
            }
        )

        print("\nFLIGHT RESULT")

        for item in result.content:
            if isinstance(item, TextContent):
                print(item.text)

        # ----------------------------------------
        # 3. READ FIXED RESOURCE
        # ----------------------------------------

        preferences = await client.read_resource(
            "travel://preferences"
        )

        print("\nTRAVEL PREFERENCES")

        for item in preferences.contents:
            if isinstance(item, TextResourceContents):
                print(item.text)

        # ----------------------------------------
        # 4. READ DYNAMIC RESOURCE
        # ----------------------------------------

        city = await client.read_resource(
            "city://Dubai/guide"
        )

        print("\nCITY GUIDE")

        for item in city.contents:
            if isinstance(item, TextResourceContents):
                print(item.text)

        # ----------------------------------------
        # 5. GET MCP PROMPT
        # ----------------------------------------

        prompt = await client.get_prompt(
            "plan_business_trip",
            {
                "destination": "Dubai",
                "days": "5"
            }
        )

        print("\nPLANNING PROMPT")

        for message in prompt.messages:
            if isinstance(message.content, TextContent):
                print(message.content.text)


if __name__ == "__main__":
    asyncio.run(main())
