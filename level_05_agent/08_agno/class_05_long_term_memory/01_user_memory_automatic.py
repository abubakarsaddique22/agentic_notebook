"""
=====================================================================
 CLASS 05 | FILE 01: user_memory_automatic.py
=====================================================================
 CONCEPT: Long-Term Memory (User Memories) — automatic
 Kya hai : Session history sirf EK conversation ki hoti hai.
           User memory = user ke baare mein FACTS jo HAR conversation
           mein yaad rahein (naam, pasand, kaam).
             user_id="..."             -> memory kis user ki hai
             update_memory_on_run=True -> har run ke baad Agno khud
                                          (background LLM call se) naye
                                          facts nikal ke save karta hai
             add_memories_to_context   -> memories prompt mein (default ON)
 Test    : Session 1 mein baat batao -> Session 2 (bilkul NAYI chat)
           mein poocho -> yaad hona chahiye.

 Run:
     uv run python class_05_long_term_memory/01_user_memory_automatic.py
=====================================================================
"""

from agno.agent import Agent
from agno.db.sqlite import SqliteDb

from llm_setup import get_model

agent = Agent(
    name="memory_agent",
    model=get_model(),
    db=SqliteDb(db_file="tmp/class05.db"),
    update_memory_on_run=True,     # <-- long-term memory ON
    markdown=True,
)

USER = "abubakar@example.com"

# ---------- Conversation 1 ----------
agent.print_response("My name is Abubakar, I am an AI Engineer in Lahore and I love cricket.",
                     user_id=USER, session_id="chat_1")

# ---------- Conversation 2 (nayi chat, nayi session) ----------
agent.print_response("Tell me what you know about me, and suggest a weekend plan.",
                     user_id=USER, session_id="chat_2")

# ---------- Save hui memories ----------
print("\n===== USER MEMORIES =====")
for mem in agent.get_user_memories(user_id=USER) or []:
    print(f"- {mem.memory}   (topics: {mem.topics})")
