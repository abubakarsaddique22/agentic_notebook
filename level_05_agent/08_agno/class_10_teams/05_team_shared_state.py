"""
=====================================================================
 CLASS 10 | FILE 05: team_shared_state.py
=====================================================================
 CONCEPT: Team ka shared Session State + memory (db)
 Kya hai : Team ka session_state saare members SHARE karte hain.
           Member ke tool mein run_context.session_state = TEAM ki state.
           db + session_id + add_history_to_context = team ko pichli
           baat bhi yaad.
   Example: 3 lists (groceries, todo, study) — har list ka alag agent,
            lekin data ek hi jagah (team state) mein.

 Run:
     uv run python class_10_teams/05_team_shared_state.py
=====================================================================
"""

from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.run import RunContext
from agno.team import Team

from llm_setup import get_model

LISTS = ["groceries_list", "todo_list", "study_list"]


def add_item(run_context: RunContext, list_name: str, item: str) -> str:
    """Add an item to a list. list_name: groceries_list, todo_list or study_list."""
    if list_name not in LISTS:
        return f"'{list_name}' is not a valid list. Use: {LISTS}"
    run_context.session_state[list_name].append(item.lower())
    return f"{item} -> {list_name}"


def remove_item(run_context: RunContext, list_name: str, item: str) -> str:
    """Remove an item from a list."""
    items = run_context.session_state.get(list_name, [])
    if item.lower() not in items:
        return f"{item} is not in {list_name}"
    items.remove(item.lower())
    return f"{item} removed from {list_name}"


def show_list(run_context: RunContext, list_name: str) -> str:
    """Show the items in a list."""
    items = run_context.session_state.get(list_name, [])
    return f"{list_name}: {', '.join(items) if items else 'empty'}"


tools = [add_item, remove_item, show_list]

grocery_agent = Agent(name="Grocery Agent", role="Manages the groceries_list", model=get_model(), tools=tools)
todo_agent = Agent(name="Todo Agent", role="Manages the todo_list", model=get_model(), tools=tools)
study_agent = Agent(name="Study Agent", role="Manages the study_list", model=get_model(), tools=tools)

list_manager = Team(
    name="List Manager",
    model=get_model(),
    members=[grocery_agent, todo_agent, study_agent],
    db=SqliteDb(db_file="tmp/class10.db"),
    session_id="my_lists",
    session_state={"groceries_list": [], "todo_list": [], "study_list": []},
    add_session_state_to_context=True,
    add_history_to_context=True,
    num_history_runs=3,
    instructions=["Lists: groceries_list, todo_list, study_list",
                  "Look at the request and delegate to the agent for the right list"],
    markdown=True,
)

list_manager.print_response("Add milk and eggs to groceries, and 'go to the gym' to todo")
list_manager.print_response("Add 'Agno teams' to the study list")
list_manager.print_response("I bought the milk, remove it from groceries")

print("\nTEAM STATE:", list_manager.get_session_state(session_id="my_lists"))

# Interactive chat chahiye to:  list_manager.cli_app(stream=True, markdown=True)
