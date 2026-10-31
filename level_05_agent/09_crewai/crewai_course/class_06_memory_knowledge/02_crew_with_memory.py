"""
=====================================================================
 CLASS 06 | FILE 02: crew_with_memory.py
=====================================================================
 CONCEPT: Crew Memory (agents ko pichli baatein yaad rehna)
 Kya hai : Crew(memory=...) dene se:
             - har task ke baad CrewAI kaam ki baatein khud save karta hai
             - agla task / agli kickoff unhe khud "recall" karti hai
           Is file mein 2 dafa crew chalate hain:
             Run 1: customer apni pasand batata hai
             Run 2: naya sawal — agent ko Run 1 ki baat yaad honi chahiye
 Note    : memory=True bhi likh sakte ho, lekin wo default OpenAI use
           karta hai. Isliye hum Memory(...) object khud bana ke de rahe
           hain apne LLM aur local embedder ke saath.

 Run:
     uv run python class_06_memory_knowledge/02_crew_with_memory.py
=====================================================================
"""

from crewai import Agent, Task, Crew, Memory

from llm_setup import get_llm, EMBEDDER

llm = get_llm()

shared_memory = Memory(llm=llm, embedder=EMBEDDER)

support = Agent(
    role="Customer Support Agent",
    goal="Remember customer preferences and give personal replies",
    backstory="You know every customer by name.",
    llm=llm,
)

task = Task(
    description="Customer message: '{message}'. Reply to it.",
    expected_output="A friendly reply in 2-3 lines.",
    agent=support,
)

crew = Crew(agents=[support], tasks=[task], memory=shared_memory, verbose=True)

# ---------- Run 1 ----------
r1 = crew.kickoff(inputs={"message": "My name is Sara and I like white dial watches."})
print("\nRUN 1:", r1.raw)

# ---------- Run 2 (alag sawal) ----------
r2 = crew.kickoff(inputs={"message": "Suggest a watch for me. Do you remember what I like?"})
print("\nRUN 2:", r2.raw)

# Memory mein kya save hua?
print("\n===== MEMORY MEIN SAVED =====")
for m in shared_memory.recall("Sara ki pasand", limit=3):
    print("-", m.record.content)
