"""Authenticated MCP client for protected booking service."""
import os
import httpx2
from mcp import Client
from mcp.client.streamable_http import streamable_http_client
URL='http://127.0.0.1:8004/mcp'

def booking_client(role='traveler'):
    """Return an async context manager which yields a connected Client."""
    raise RuntimeError('Use authenticated_booking_client() instead')

from contextlib import asynccontextmanager
@asynccontextmanager
async def authenticated_booking_client(role='traveler'):
    name='BOOKING_ADMIN_TOKEN' if role=='admin' else 'BOOKING_USER_TOKEN'
    token=os.getenv(name)
    if not token: raise RuntimeError(f'{name} missing')
    async with httpx2.AsyncClient(headers={'Authorization':f'Bearer {token}'},timeout=httpx2.Timeout(30.0,read=300.0)) as http:
        async with Client(streamable_http_client(URL,http_client=http)) as client:
            yield client
