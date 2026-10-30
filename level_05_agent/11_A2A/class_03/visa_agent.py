# ==========================================================
# CLASS 03 - visa_agent.py   (CHALLENGE SOLUTION)
# Third A2A SERVER: the Visa Agent (port 10001)
# Only 4 things change vs. hotel_agent.py: executor text, skill, card, port.
# Run:  python visa_agent.py
# ==========================================================
import uvicorn

from a2a.helpers import get_message_text, new_text_message
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes import create_agent_card_routes, create_jsonrpc_routes
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentInterface, AgentSkill
from starlette.applications import Starlette

PORT = 10001


class VisaAgentExecutor(AgentExecutor):
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        query = get_message_text(context.message) if context.message else ""
        result = (
            "Visa Agent result:\n"
            "UAE tourist visa (30 days)\n"
            "Documents: passport (6+ months valid), photo, return ticket, hotel booking\n"
            "Processing time: 3-5 working days (dummy data)\n"
            f"\nReceived task: {query}"
        )
        await event_queue.enqueue_event(new_text_message(result))

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise NotImplementedError("Cancellation is not supported.")


skill = AgentSkill(
    id="check_visa",
    name="Check Visa Requirements",
    description="Explains visa requirements for a destination.",
    input_modes=["text/plain"],
    output_modes=["text/plain"],
    tags=["travel", "visa"],
    examples=["What visa do I need for Dubai?"],
)

agent_card = AgentCard(
    name="Visa Agent",
    description="Specialized agent for visa requirements.",
    version="1.0.0",
    default_input_modes=["text/plain"],
    default_output_modes=["text/plain"],
    capabilities=AgentCapabilities(streaming=False, extended_agent_card=False),
    supported_interfaces=[
        AgentInterface(
            protocol_binding="JSONRPC",
            url=f"http://127.0.0.1:{PORT}",
            protocol_version="1.0",
        )
    ],
    skills=[skill],
)

request_handler = DefaultRequestHandler(
    agent_executor=VisaAgentExecutor(),
    task_store=InMemoryTaskStore(),
    agent_card=agent_card,
)

app = Starlette(
    routes=[
        *create_agent_card_routes(agent_card),
        *create_jsonrpc_routes(request_handler, "/"),
    ]
)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=PORT)
