"""
=====================================================================
 CLASS 06 | FILE 01: memory_basics.py
=====================================================================
 CONCEPT: Memory (standalone)
 Kya hai : Memory = agent ki "yaadasht". Jo baat aaj batao, wo kal
           bhi yaad rahe (disk pe save hoti hai).
           CrewAI ki naye version mein ek hi "Memory" class hai:
             memory.remember("baat")      -> yaad karo (save)
             memory.recall("sawal")       -> yaad se dhoondo (search)
           Save karte waqt LLM khud decide karta hai ke baat kitni
           important hai aur kis category ki hai.
 Kaise dhoondti hai: meaning se (semantic search) + kitni nayi hai
           (recency) + kitni important hai (importance).

 Run:
     uv run python class_06_memory_knowledge/01_memory_basics.py
=====================================================================
"""

from crewai import Memory

from llm_setup import get_llm, EMBEDDER

memory = Memory(
    llm=get_llm(temperature=0.0),   # save karte waqt analysis ke liye
    embedder=EMBEDDER,              # text -> vectors (local onnx)
)

# 1) Kuch baatein yaad karwao
memory.remember("Customer Ali likes black leather straps.")
memory.remember("Customer Ali lives in Karachi and always pays cash on delivery.")
memory.remember("The store's return policy is 7 days.")

# 2) Sawal pooch ke yaad se nikalo
matches = memory.recall("Which strap does Ali like?", limit=3)

print("\n===== RECALL RESULTS =====")
for m in matches:
    print(f"score={m.score:.2f} | {m.record.content}")

# ------------------------------------------------------------------
# Memory sab kuch bhoolni ho:  memory.reset()
# Ya terminal mein:            crewai reset-memories --all
# ------------------------------------------------------------------
