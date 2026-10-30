"""Authenticated protocol-level booking health check."""
import asyncio
import os
import sys
import httpx2
from mcp import Client
from mcp.client.streamable_http import streamable_http_client

async def main():
    token = os.environ['BOOKING_USER_TOKEN']
    url = os.environ.get('BOOKING_MCP_URL', 'http://127.0.0.1:8004/mcp')
    async with asyncio.timeout(8):
        async with httpx2.AsyncClient(headers={'Authorization': f'Bearer {token}'}) as http:
            async with Client(streamable_http_client(url, http_client=http)) as c:
                assert (await c.list_tools()).tools

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except Exception as exc:
        print('Unhealthy:', type(exc).__name__, file=sys.stderr)
        sys.exit(1)
