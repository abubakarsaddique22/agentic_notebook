"""
=====================================================================
 CLASS 05 | FILE 02: agentic_memory.py
=====================================================================
 CONCEPT: Agentic Memory (agent khud decide kare kya yaad rakhna hai)
 Kya hai : enable_agentic_memory=True -> agent ko ek memory TOOL milta
           hai. Wo khud faisla karta hai:
             - kab naya fact save karna hai
             - kab purana fact update karna hai ("ab main Karachi mein hoon")
             - kab bhoolna hai ("meri pasand bhool jao")
 Farq    : update_memory_on_run -> HAR run ke baad extra LLM call
           enable_agentic_memory -> sirf zaroorat pe (tool call)

 Run:
     uv run python class_05_long_term_memory/02_agentic_memory.py
=====================================================================
"""

from agno.agent import Agent
from agno.db.sqlite import SqliteDb

from llm_setup import get_model

agent = Agent(
    name="agentic_memory_agent",
    model=get_model(),
    db=SqliteDb(db_file="tmp/class05.db"),
    enable_agentic_memory=True,    # <-- agent khud memory manage karega
    markdown=True,
)

USER = "sara@example.com"


def show_memories(title: str):
    print(f"\n----- {title} -----")
    for mem in agent.get_user_memories(user_id=USER) or []:
        print("-", mem.memory)


agent.print_response("I like white dial watches and I live in Islamabad.", user_id=USER)
show_memories("Before")

agent.print_response("I have moved to Karachi now, please update that.", user_id=USER)
show_memories("After update")

agent.print_response("Forget my watch preference.", user_id=USER)
show_memories("After forgetting")
