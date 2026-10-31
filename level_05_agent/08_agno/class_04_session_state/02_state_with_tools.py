"""
=====================================================================
 CLASS 04 | FILE 02: state_with_tools.py
=====================================================================
 CONCEPT: Tools jo Session State padhte/badalte hain (CRUD)
 Kya hai : Tool function ka pehla parameter `run_context: RunContext`
           rakho — Agno khud bharta hai (model ko ye nazar nahi aata).
           run_context.session_state se state parho aur badlo.
           Har session ki apni list hoti hai (fruits vs dairy).

   Add / Remove / List / Clear  ->  session_state["cart"]

 Run:
     uv run python class_04_session_state/02_state_with_tools.py
=====================================================================
"""

from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.run import RunContext

from llm_setup import get_model


def add_item(run_context: RunContext, item: str) -> str:
    """Add an item to the cart."""
    cart = run_context.session_state["cart"]
    item = item.lower().strip()
    if item in cart:
        return f"{item} is already in the cart"
    cart.append(item)
    return f"{item} added to the cart"


def remove_item(run_context: RunContext, item: str) -> str:
    """Remove an item from the cart."""
    cart = run_context.session_state["cart"]
    item = item.lower().strip()
    if item not in cart:
        return f"{item} is not in the cart"
    cart.remove(item)
    return f"{item} removed from the cart"


def list_items(run_context: RunContext) -> str:
    """Show all items in the cart."""
    cart = run_context.session_state["cart"]
    return "Cart: " + ", ".join(cart) if cart else "Cart is empty"


def clear_cart(run_context: RunContext) -> str:
    """Clear the whole cart."""
    run_context.session_state["cart"].clear()
    return "Cart cleared"


agent = Agent(
    name="cart_agent",
    model=get_model(),
    db=SqliteDb(db_file="tmp/class04.db"),
    session_state={"cart": []},             # shuru mein khali cart
    tools=[add_item, remove_item, list_items, clear_cart],
    instructions=["Always use the tools to change or view the cart",
                  "If a tool fails, never claim the task was done"],
    add_session_state_to_context=True,
    markdown=True,
)

# ---------- Session 1: watches cart ----------
agent.print_response("Add the classic steel watch and the gold executive", session_id="watch_cart")
agent.print_response("Remove the classic steel and show me the cart", session_id="watch_cart")

# ---------- Session 2: alag cart ----------
agent.print_response("Add a leather strap", session_id="strap_cart")

print("\nwatch_cart:", agent.get_session_state(session_id="watch_cart"))
print("strap_cart:", agent.get_session_state(session_id="strap_cart"))
