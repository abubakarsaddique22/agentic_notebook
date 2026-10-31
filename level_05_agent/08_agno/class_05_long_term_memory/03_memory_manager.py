"""
=====================================================================
 CLASS 05 | FILE 03: memory_manager.py
=====================================================================
 CONCEPT: MemoryManager (memory ko customize karna)
 Kya hai : MemoryManager decide karta hai ke kya save ho aur kaise.
           Isay alag se bana ke:
             model=...                    -> memory ke liye sasta/alag model
             memory_capture_instructions  -> SIRF kya yaad rakhna hai
                                             (e.g. sirf shopping pasand,
                                              personal/sensitive baatein nahi)
             delete_memories / clear_memories -> permissions
           Phir Agent(memory_manager=...) mein do.
           MemoryManager ko akela bhi use kar sakte ho (bina agent ke).

 Run:
     uv run python class_05_long_term_memory/03_memory_manager.py
=====================================================================
"""

from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.memory import MemoryManager

from llm_setup import get_model

db = SqliteDb(db_file="tmp/class05.db")

memory_manager = MemoryManager(
    model=get_model(),
    db=db,
    memory_capture_instructions=(
        "Only remember the customer's SHOPPING preferences: brand, strap, color, budget. "
        "Never save personal details like health, money (salary) or passwords."
    ),
    delete_memories=True,
)

USER = "bilal@example.com"

# ---------- 1) MemoryManager akela ----------
memory_manager.create_user_memories(
    message="My budget is 8000 and I want a leather strap. My salary is 100,000.",
    user_id=USER,
)
print("Direct memories:")
for mem in memory_manager.get_user_memories(user_id=USER) or []:
    print("-", mem.memory)

# ---------- 2) Agent ke saath ----------
agent = Agent(
    name="shopping_agent",
    model=get_model(),
    db=db,
    memory_manager=memory_manager,
    update_memory_on_run=True,
    markdown=True,
)
agent.print_response("Suggest a watch for me.", user_id=USER)

# ---------- 3) Memory saaf karna ----------
memory_manager.clear_user_memories(user_id=USER)
print("\nClear ke baad:", memory_manager.get_user_memories(user_id=USER))
