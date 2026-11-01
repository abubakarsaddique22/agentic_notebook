"""EASY VERSION: Booking server (8004) se token ke saath connect hone wala client."""
import os
from contextlib import asynccontextmanager

import httpx2
from mcp import Client
from mcp.client.streamable_http import streamable_http_client

URL = "http://127.0.0.1:8004/mcp"

# Kaunsa role, .env mein kaunsa token
TOKEN_NAMES = {
    "traveler": "BOOKING_USER_TOKEN",
    "admin": "BOOKING_ADMIN_TOKEN",
}


@asynccontextmanager
async def authenticated_booking_client(role: str = "traveler"):
    """Token laga kar server se connect karta hai aur client wapas deta hai.
    Use:  async with authenticated_booking_client("admin") as client: ..."""

    # ---------- Step 1: sahi token lo ----------
    if role not in TOKEN_NAMES:
        raise ValueError("role sirf 'traveler' ya 'admin' ho sakta hai")

    token_name = TOKEN_NAMES[role]
    token = os.getenv(token_name)

    if not token:
        raise RuntimeError(f"{token_name} missing in .env")

    # ---------- Step 2: har request ke saath token bhejo ----------
    headers = {"Authorization": f"Bearer {token}"}
    timeout = httpx2.Timeout(30.0, read=300.0)  # connect 30 sec, jawab ka intezar 5 min

    async with httpx2.AsyncClient(headers=headers, timeout=timeout) as http:

        # ---------- Step 3: is HTTP connection se MCP client banao ----------
        async with Client(streamable_http_client(URL, http_client=http)) as client:
            yield client  # client istemaal karne wale ko de do
        # "async with" khatam hote hi dono connections khud band ho jaate hain