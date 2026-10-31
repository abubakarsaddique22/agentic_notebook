"""
=====================================================================
 CLASS 04 | FILE 03: dependencies_context.py
=====================================================================
 CONCEPT: Dependencies (run time pe fresh data prompt mein daalna)
 Kya hai : dependencies={...} mein values YA functions do.
           Function har run pe chalta hai -> hamesha FRESH data.
             add_dependencies_to_context=True -> sab dependencies
                                                 prompt mein jayengi
             instructions mein {naam}          -> sirf wahi value
           Tool bhi run_context.dependencies se parh sakta hai.
 Kyun    : User profile DB se, aaj ke offers, live stock — har sawal
           se pehle khud load ho jaye.

 Run:
     uv run python class_04_session_state/03_dependencies_context.py
=====================================================================
"""

import json
from datetime import datetime

from agno.agent import Agent

from llm_setup import get_model


def get_todays_offer() -> str:
    """Har run pe chalega — asal mein ye database se aata."""
    day = datetime.now().strftime("%A")
    return f"{day} special: 15% off on Classic Steel"


def get_user_profile() -> str:
    return json.dumps({"name": "Bilal", "past_orders": 3, "likes": "leather straps"})


agent = Agent(
    name="sales_agent",
    model=get_model(),
    dependencies={
        "offer": get_todays_offer,          # function -> har dafa fresh
        "user_profile": get_user_profile,
        "store_name": "TimeHouse",          # simple value
    },
    instructions=["You are the sales agent of {store_name}",
                  "Today's offer: {offer}",
                  "Give a personal suggestion based on the user profile"],
    add_dependencies_to_context=True,
    markdown=True,
)

agent.print_response("Suggest a watch for me.")
