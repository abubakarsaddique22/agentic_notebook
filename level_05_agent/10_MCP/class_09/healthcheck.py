"""Protocol-level check; no external LLM/API call; works in container network."""
import asyncio
import os
import sys
from mcp import Client

async def main():
    url = os.environ['HEALTH_MCP_URL']
    async with asyncio.timeout(8):
        async with Client(url) as client:
            tools = await client.list_tools()
            if not tools.tools:
                raise RuntimeError('No MCP tools')

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except Exception as exc:
        print('Unhealthy:', type(exc).__name__, file=sys.stderr)
        sys.exit(1)
