"""
=====================================================================
 CLASS 03 | FILE 01: session_history.py
=====================================================================
 CONCEPT: Short-Term Memory (Session + Chat History)
 Kya hai : By default agent har sawal ko NAYA samajhta hai — pichli
           baat yaad nahi. Short-term memory ke liye 3 cheezein:
             db=SqliteDb(...)            -> baat-cheet disk pe save
             session_id="..."           -> ek conversation ka ID
                                           (ChatGPT ki left side ki ek chat)
             add_history_to_context=True -> pichle messages prompt mein
             num_history_runs=5          -> sirf last 5 sawal-jawab
                                           (tokens bachane ke liye)

 Run:
     uv run python class_03_short_term_memory/01_session_history.py
=====================================================================
"""

from agno.agent import Agent
from agno.db.sqlite import SqliteDb

from llm_setup import get_model

db = SqliteDb(db_file="tmp/class03.db")      # course folder mein tmp/ ban jayega

agent = Agent(
    name="chat_agent",
    model=get_model(),
    db=db,
    session_id="session_01",
    add_history_to_context=True,
    num_history_runs=5,
    markdown=True,
)

agent.print_response("My name is Abubakar and I am an AI Engineer.")
agent.print_response("Tell me a short joke.")
agent.print_response("Tell me, who am I?")      # pichli baat yaad honi chahiye

# ---------- Saari history dekho ----------
print("\n===== CHAT HISTORY =====")
for msg in agent.get_chat_history(session_id="session_01"):
    if msg.role != "system":
        print(f"[{msg.role}] {str(msg.content)[:80]}")
