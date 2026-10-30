import asyncio
from mcp import Client

SERVERS = {'Travel': 'http://127.0.0.1:8001/mcp', 'Policy': 'http://127.0.0.1:8002/mcp', 'Work': 'http://127.0.0.1:8003/mcp'}

async def main():
    for name, url in SERVERS.items():
        try:
            async with Client(url) as client:
                tools = await client.list_tools()
                print(f'{name} OK ({url}): {[tool.name for tool in tools.tools]}')
        except Exception as exc:
            print(f'{name} FAILED ({url}): {type(exc).__name__}: {exc}')

if __name__ == '__main__':
    asyncio.run(main())
