# Pydantic Field applies ticket input length constraints.
# Local test principal (CLI is not verified authentication).
from contextvars import ContextVar  # Async/thread-local verified caller identity hold karta hai.
from dataclasses import dataclass  # Principal value object define karta hai.
from pydantic import BaseModel, Field  # Tool arguments validate karta hai.

@dataclass(frozen=True)
class Principal:
    user_id: str  # Verified app identity; LLM arguments se nahi leni.
    role: str = 'viewer'  # Server-controlled role.
    tenant_id: str = 'public'  # Server-owned tenant context.

# Default identity least-privilege hai; prompt messages role overwrite nahi kar sakte.
_current = ContextVar('agent_principal', default=Principal('anonymous', 'viewer'))

class TicketArgs(BaseModel):
    title: str = Field(min_length=5, max_length=120)  # Ticket title.
    description: str = Field(min_length=10, max_length=1200)  # Ticket details.

def current_principal() -> Principal:
    return _current.get()

def set_principal(principal: Principal):
    """Returns ContextVar token; caller must reset in finally."""
    return _current.set(principal)

def reset_principal(token):
    _current.reset(token)

def can_request_ticket(principal: Principal) -> bool:
    # Tool arguments/request text se caller role kabhi grant nahi hota.
    return principal.role in {'operator','admin'} and principal.user_id != 'anonymous'

def can_approve(principal: Principal) -> bool:
    return principal.role == 'admin' and principal.user_id != 'anonymous'
