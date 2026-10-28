
import asyncio
import sys
from pathlib import Path

from mcp import Client, StdioServerParameters
from mcp.types import TextContent, TextResourceContents


async def main():

    # ==================================================
    # 1. CONNECT TO MCP SERVER
    # ==================================================

    server_path = Path(__file__).parent / "server.py"

    params = StdioServerParameters(
        command=sys.executable,
        args=[str(server_path)]
    )

    async with Client(params) as client:

        print("\nCONNECTED TO MCP SERVER")


        # ==================================================
        # 2. LIST TOOLS
        # ==================================================

        tools = await client.list_tools()

        print("\nAVAILABLE TOOLS")

        for tool in tools.tools:
            print("-", tool.name)


        # ==================================================
        # 3. LIST FIXED RESOURCES
        # ==================================================

        resources = await client.list_resources()

        print("\nAVAILABLE RESOURCES")

        for resource in resources.resources:
            print("-", resource.uri)


        # ==================================================
        # 4. READ FIXED RESOURCE
        # ==================================================

        result = await client.read_resource(
            "travel://preferences"
        )

        print("\nTRAVEL PREFERENCES")

        for item in result.contents:
            if isinstance(item, TextResourceContents):
                print(item.text)


        # ==================================================
        # 5. LIST RESOURCE TEMPLATES
        # ==================================================

        templates = await client.list_resource_templates()

        print("\nRESOURCE TEMPLATES")

        for template in templates.resource_templates:
            print("-", template.uri_template)


        # ==================================================
        # 6. READ DYNAMIC RESOURCE
        # ==================================================

        city_result = await client.read_resource(
            "city://Dubai/guide"
        )

        print("\nCITY GUIDE")

        for item in city_result.contents:
            if isinstance(item, TextResourceContents):
                print(item.text)


        # ==================================================
        # 7. LIST PROMPTS
        # ==================================================

        prompts = await client.list_prompts()

        print("\nAVAILABLE PROMPTS")

        for prompt in prompts.prompts:
            print("-", prompt.name)


        # ==================================================
        # 8. GET PROMPT
        # ==================================================

        prompt_result = await client.get_prompt(
            "plan_business_trip",
            {
                "destination": "Dubai",
                "days": "5"
            }
        )

        print("\nBUSINESS TRIP PROMPT")

        for message in prompt_result.messages:
            if isinstance(message.content, TextContent):
                print(message.content.text)


        # ==================================================
        # 9. CALL TOOL
        # ==================================================

        flight_result = await client.call_tool(
            "search_flights",
            {
                "origin": "Lahore",
                "destination": "Dubai"
            }
        )

        print("\nFLIGHT SEARCH RESULT")

        for item in flight_result.content:
            if isinstance(item, TextContent):
                print(item.text)


if __name__ == "__main__":
    asyncio.run(main())
