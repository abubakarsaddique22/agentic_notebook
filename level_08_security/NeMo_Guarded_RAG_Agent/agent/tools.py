from langchain_core.tools import tool  # LLM-callable typed tool decorator.
from pydantic import BaseModel, Field  # Tool argument validation.
from rag.store import retrieve
from agent.identity import current_principal, TicketArgs, can_request_ticket
from agent.tickets import request_ticket
from config.actions import inspect_tool_documents

class SearchArgs(BaseModel):
    query: str = Field(min_length=2,max_length=500,description='Question about company policies')

@tool(args_schema=SearchArgs)
def search_knowledge(query: str) -> str:
    """Search indexed company policy documents and return attributed sources."""
    docs = retrieve(query, tenant_id=current_principal().tenant_id)
    if not docs: return 'No relevant policy documents found.'
    safe_docs = [d for d in docs if inspect_tool_documents(d.page_content)]
    if not safe_docs: return 'DENIED: retrieved content failed NeMo retrieval policy.'
    return "\n\n".join(
        f'<untrusted_document source="{d.metadata.get("source", "unknown")}">\n{d.page_content}\n</untrusted_document>'
        for d in safe_docs
    )

class MultiplyArgs(BaseModel):
    a: float = Field(description='First number')
    b: float = Field(description='Second number')

@tool(args_schema=MultiplyArgs)
def multiply(a: float,b: float) -> float:
    """Multiply numeric inputs without external side effects."""
    return a*b


@tool(args_schema=TicketArgs)
def request_support_ticket(title: str, description: str) -> str:
    """Request a support ticket for HUMAN approval; never execute the ticket automatically."""
    principal = current_principal()  # Identity application se aati hai, user prompt se nahi.
    if not can_request_ticket(principal):
        return 'DENIED: only verified operators may request support tickets.'
    ticket_id = request_ticket(principal, title=title, description=description)
    return f'Ticket request #{ticket_id} is PENDING HUMAN APPROVAL. No action was executed.'

TOOLS = [search_knowledge,multiply,request_support_ticket]  # LLM ko direct email/network/approval tool nahi diya gaya; request creates pending record only.
