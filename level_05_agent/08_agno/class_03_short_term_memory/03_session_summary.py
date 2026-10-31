"""
=====================================================================
 CLASS 03 | FILE 03: session_summary.py
=====================================================================
 CONCEPT: Session Summaries + Past session search
 Problem : Lambi chat mein poori history bhejna mehnga hai (tokens),
           aur num_history_runs=5 se purani baatein "bhool" jati hain.
 Hal 1   : enable_session_summaries=True -> har run ke baad Agno poori
           chat ka chhota SUMMARY banata hai. add_session_summary_to_
           context=True se wo summary prompt mein jata hai.
 Hal 2   : search_past_sessions=True -> agent PURANI sessions (doosri
           chats) mein bhi dhoond sakta hai.
 Hal 3   : read_chat_history=True -> agent ko tool milta hai jis se wo
           zaroorat pe khud poori history parhe.

 Run:
     uv run python class_03_short_term_memory/03_session_summary.py
=====================================================================
"""

from agno.agent import Agent
from agno.db.sqlite import SqliteDb

from llm_setup import get_model

agent = Agent(
    name="summary_agent",
    model=get_model(),
    db=SqliteDb(db_file="tmp/class03.db"),
    session_id="planning_chat",
    enable_session_summaries=True,          # summary banao
    add_session_summary_to_context=True,    # summary prompt mein do
    add_history_to_context=True,
    num_history_runs=2,                     # sirf last 2 runs + summary
    read_chat_history=True,                 # zaroorat pe poori history tool se
    markdown=True,
)

agent.print_response("I am opening an online watch store with a budget of 200,000 PKR.")
agent.print_response("I want to do marketing on Instagram.")
agent.print_response("Give me a plan for the first 3 months in 5 bullets.")

summary = agent.get_session_summary(session_id="planning_chat")
print("\n===== SESSION SUMMARY =====")
print(summary.summary if summary else "Abhi summary nahi bani")
