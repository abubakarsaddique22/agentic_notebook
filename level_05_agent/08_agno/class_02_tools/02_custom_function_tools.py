"""
=====================================================================
 CLASS 02 | FILE 02: custom_function_tools.py
=====================================================================
 CONCEPT: Custom Tool = simple Python function
 Kya hai : Agno mein koi bhi Python function seedha tool ban jata hai —
           bas tools=[my_function] likh do.
 ZAROORI :
   - Docstring = tool ki description (model isi se samajhta hai kab
     use karna hai)
   - Type hints (str, int) = model ko pata chalta hai kya input dena hai
   - Return hamesha string (ya JSON string) rakho — model text parhta hai

 Run:
     uv run python class_02_tools/02_custom_function_tools.py
=====================================================================
"""

import json

from agno.agent import Agent

from llm_setup import get_model

# Fake database
WATCHES = {
    "classic steel": {"price": 4500, "stock": 12},
    "black chrono": {"price": 6800, "stock": 0},
    "gold executive": {"price": 9999, "stock": 5},
}


def check_stock(watch_name: str) -> str:
    """Returns the price and stock of a watch.

    Args:
        watch_name: name of the watch, e.g. 'classic steel'
    """
    info = WATCHES.get(watch_name.lower().strip())
    if info is None:
        return f"'{watch_name}' not found. Available: {list(WATCHES)}"
    return json.dumps(info)


def delivery_charges(city: str, order_total: int) -> str:
    """Returns delivery charges. Inputs: city name and order total (PKR)."""
    if order_total >= 3000:
        return "Free delivery"
    return "250 PKR" if city.lower() == "lahore" else "350 PKR"


agent = Agent(
    name="store_assistant",
    model=get_model(),
    tools=[check_stock, delivery_charges],
    instructions=["Always check price and stock with the tool, never guess"],
    markdown=True,
)

agent.print_response("Is the gold executive available? How much is delivery to Karachi?", stream=True)
