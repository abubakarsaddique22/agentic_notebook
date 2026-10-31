"""
=====================================================================
 CLASS 03 | FILE 02: multiple_sessions.py
=====================================================================
 CONCEPT: Multiple Sessions (alag alag conversations)
 Kya hai : Ek hi agent, alag session_id = alag conversation. Har
           session ki history alag rehti hai — jaise ChatGPT mein
           "Transformer chat" aur "RAG chat" alag hain.
           session_id print_response / run ke andar bhi de sakte ho.
           Program band karke dobara chalao — db se purani baat
           wapas mil jayegi (same session_id do).

 Run:
     uv run python class_03_short_term_memory/02_multiple_sessions.py
=====================================================================
"""

from agno.agent import Agent
from agno.db.sqlite import SqliteDb

from llm_setup import get_model

agent = Agent(
    name="study_buddy",
    model=get_model(),
    db=SqliteDb(db_file="tmp/class03.db"),
    add_history_to_context=True,
    num_history_runs=5,
    markdown=True,
)

# ---------- Session 1: Transformers ----------
agent.print_response("Explain the Transformer architecture in 50 words.", session_id="transformer_chat")
agent.print_response("Self-attention in one line?", session_id="transformer_chat")

# ---------- Session 2: RAG ----------
agent.print_response("What is RAG? 50 words.", session_id="rag_chat")

# ---------- Wapas Session 1 ----------
agent.print_response("What is this conversation about?", session_id="transformer_chat")
agent.print_response("What is this conversation about?", session_id="rag_chat")

# Har session mein kitne messages hain
for sid in ["transformer_chat", "rag_chat"]:
    print(f"{sid}: {len(agent.get_chat_history(session_id=sid))} messages")
