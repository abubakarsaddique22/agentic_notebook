# ==========================================================
# CLASS 03 - travel_orchestrator.py
# The ORCHESTRATOR (A2A client) that delegates work to many agents.
# Needs running: flight_agent.py (9999), hotel_agent.py (10000)
#                and optionally visa_agent.py (10001)
# Run:  python travel_orchestrator.py
#
# Improvements over the class demo:
#   1. Clean text output  (response.HasField("message") instead of isinstance)
#   2. try/except         (one agent down does not crash the whole plan)
#   3. Parallel calls     (asyncio.gather -> all agents work at the same time)
# ==========================================================
import asyncio
import time

import httpx

from a2a.client import A2ACardResolver, ClientConfig, create_client
from a2a.helpers import get_message_text, new_text_message
from a2a.types import Role, SendMessageRequest

# Which agent gets which sub-task
DELEGATION_PLAN = [
    ("http://127.0.0.1:9999",  "Find good flights from Bangalore to Dubai."),
    ("http://127.0.0.1:10000", "Find a 4-star hotel in Dubai for 5 nights."),
    ("http://127.0.0.1:10001", "What visa does an Indian citizen need for Dubai?"),
]


async def call_remote_agent(base_url: str, task_text: str) -> tuple[str, str]:
    """Discover an agent, send it one message, return (agent_name, reply_text)."""
    try:
        async with httpx.AsyncClient() as httpx_client:
            # 1) Discovery: GET the Agent Card
            resolver = A2ACardResolver(httpx_client=httpx_client, base_url=base_url)
            agent_card = await resolver.get_agent_card()
            print(f"Discovered: {agent_card.name:<12} skills={[s.name for s in agent_card.skills]}")

            # 2) Create a client from the card
            client = await create_client(
                agent=agent_card,
                client_config=ClientConfig(streaming=False),
            )
            try:
                # 3) SendMessage
                request = SendMessageRequest(
                    message=new_text_message(task_text, role=Role.ROLE_USER)
                )
                async for response in client.send_message(request):
                    # FIX: the SDK yields a StreamResponse wrapper, not a Message.
                    if response.HasField("message"):
                        return agent_card.name, get_message_text(response.message)
                    return agent_card.name, str(response)
            finally:
                await client.close()

        return agent_card.name, "No response received."

    except Exception as e:
        return base_url, f"[SKIPPED] Agent not reachable ({type(e).__name__})"


async def main():
    print("=" * 65)
    print("TRAVEL ORCHESTRATOR AGENT")
    print("=" * 65)
    print("USER REQUEST: Plan a 5-day Dubai trip from Bangalore. "
          "I need a flight, a 4-star hotel and visa info.\n")

    start = time.perf_counter()

    # All agents are called AT THE SAME TIME (parallel delegation)
    results = await asyncio.gather(
        *(call_remote_agent(url, task) for url, task in DELEGATION_PLAN)
    )

    for agent_name, reply in results:
        print("\n" + "=" * 65)
        print(f"{agent_name.upper()} RESPONSE")
        print("=" * 65)
        print(reply)

    print("\n" + "=" * 65)
    print("FINAL ORCHESTRATED RESULT")
    print("=" * 65)
    print(f"Delegated to {len(DELEGATION_PLAN)} independent A2A agents "
          f"in {time.perf_counter() - start:.2f} seconds.")


if __name__ == "__main__":
    asyncio.run(main())
