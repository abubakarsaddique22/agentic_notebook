
import asyncio
from mcp import Client

URL = "http://127.0.0.1:8001/mcp"


async def main():

    # Connect MCP Server
    async with Client(URL) as client:

        # 1. List available tools
        tools = await client.list_tools()

        for tool in tools.tools:
            print("Tool:", tool.name)

        # 2. Call weather tool
        for city in ["Dubai", "Lahore", "zzzznotacity123"]:

            weather = await client.call_tool(
                "get_live_weather",
                {"city": city}
            )

            print(f"\nWeather for {city}:")
            print(weather.content)

        # 3. Read MCP Resource
        resource = await client.read_resource(
            "travel://preferences"
        )

        print("\nTravel Preferences:")
        print(resource.contents)

        # 4. Get MCP Prompt
        prompt = await client.get_prompt(
            "plan_business_trip",
            {
                "destination": "Dubai",
                "days": "5"
            }
        )

        print("\nBusiness Trip Prompt:")
        print(prompt.messages)


asyncio.run(main())
