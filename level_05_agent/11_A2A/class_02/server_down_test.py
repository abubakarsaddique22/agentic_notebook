# ==========================================================
# CLASS 02 - server_down_test.py
# What happens if the remote agent is NOT running?
# Stop flight_agent.py first (Ctrl + C), then run:  python server_down_test.py
# ==========================================================
import asyncio

import httpx

from a2a.client import A2ACardResolver


async def main():
    async with httpx.AsyncClient() as httpx_client:
        resolver = A2ACardResolver(httpx_client=httpx_client, base_url="http://127.0.0.1:9999")
        try:
            card = await resolver.get_agent_card()
            print("Agent is UP:", card.name)
        except Exception as e:
            # Discovery fails -> the orchestrator must handle this gracefully
            print("Agent is DOWN. Error type:", type(e).__name__)
            print("Lesson: always wrap remote agent calls in try/except.")


asyncio.run(main())
