"""
=====================================================================
 CLASS 04 | FILE 01: session_state.py
=====================================================================
 CONCEPT: Session State (agent state)
 Kya hai : Chat history = jo BOLA gaya. Session state = structured DATA
           (dict) jo conversation ke saath rehta hai, jaise:
             {"name": "Ali", "cart": ["watch"], "language": "urdu"}
   session_state={...}               -> shuru ki values
   add_session_state_to_context=True -> agent ko state dikhti hai
   instructions mein {name} likho     -> state ki value khud bhar jati hai
   run(..., session_state={...})      -> beech mein state update
   agent.get_session_state()          -> state parho
 Note    : db dene se state save rehti hai (program band ho tab bhi).

 Run:
     uv run python class_04_session_state/01_session_state.py
=====================================================================
"""

from agno.agent import Agent
from agno.db.sqlite import SqliteDb

from llm_setup import get_model

agent = Agent(
    name="personal_assistant",
    model=get_model(),
    db=SqliteDb(db_file="tmp/class04.db"),
    session_id="state_demo",
    user_id="user_a",
    session_state={"name": "Abubakar", "city": "Lahore", "language": "Roman Urdu"},
    instructions=["The user's name is {name} and they live in {city}",   # {} = state se
                  "Always reply in {language}"],
    add_session_state_to_context=True,
    markdown=True,
)

agent.print_response("Tell me my name and my city.")

# State update karo (e.g. user ne profile badli)
agent.print_response("Now tell me my name and my city.",
                     session_state={"name": "Sara", "city": "Karachi", "language": "English"})

print("\nSaved state:", agent.get_session_state(session_id="state_demo"))
