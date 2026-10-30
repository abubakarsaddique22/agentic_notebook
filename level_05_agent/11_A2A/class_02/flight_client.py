# ==========================================================
# CLASS 02 - flight_client.py
# Your first A2A CLIENT: discover the Flight Agent and send it messages
# Needs: class_01/flight_agent.py running in another terminal
# Run:  python flight_client.py
# ==========================================================
import asyncio

import httpx

from a2a.client import A2ACardResolver, ClientConfig, create_client
from a2a.helpers import get_message_text, new_text_message
from a2a.types import Role, SendMessageRequest

FLIGHT_AGENT_URL = "http://127.0.0.1:9999"


async def ask_flight_agent(questions: list[str]) -> None:
    async with httpx.AsyncClient() as httpx_client:

        # ---- STEP 1: DISCOVERY - download the Agent Card ----
        resolver = A2ACardResolver(httpx_client=httpx_client, base_url=FLIGHT_AGENT_URL)
        agent_card = await resolver.get_agent_card()

        print(f"Discovered Agent : {agent_card.name}")
        print(f"Description      : {agent_card.description}")

        # ---- STEP 2: READ SKILLS - can this agent do our job? ----
        skill_ids = [s.id for s in agent_card.skills]
        print("Skills           :", [s.name for s in agent_card.skills])
        if "search_flights" not in skill_ids:
            print("This agent cannot search flights. Stopping.")
            return

        # ---- STEP 3: CREATE A2A CLIENT from the card ----
        # The client reads the card and picks the right binding (JSON-RPC here).
        client = await create_client(
            agent=agent_card,
            client_config=ClientConfig(streaming=False),
        )

        try:
            # ---- STEP 4: SEND MESSAGE(S) ----
            for q in questions:
                message = new_text_message(q, role=Role.ROLE_USER)
                request = SendMessageRequest(message=message)

                print("\n>>> YOU  :", q)
                async for response in client.send_message(request):
                    # The SDK returns a StreamResponse wrapper.
                    # Our agent replies with a direct Message (no Task).
                    if response.HasField("message"):
                        print("<<< AGENT:", get_message_text(response.message))
                    elif response.HasField("task"):
                        print("<<< AGENT created a Task:", response.task.id)
        finally:
            await client.close()


if __name__ == "__main__":
    asyncio.run(
        ask_flight_agent(
            [
                "Find good flights from Bangalore to Dubai.",
                "Cheapest flight from Lahore to Dubai next Friday?",
            ]
        )
    )
