"""
=====================================================================
 CLASS 02 | FILE 01: agent_attributes.py
=====================================================================
 CONCEPT: Agent ki important settings (attributes)
 Kya hai : role/goal/backstory ke ilawa agent ko control karne ke
           liye kuch aur settings hain:
             max_iter          -> agent zyada se zyada kitni dafa sochega
                                  (infinite loop se bachata hai)
             max_execution_time-> seconds mein time limit
             max_rpm           -> 1 minute mein max LLM calls (free
                                  API ki rate limit se bachne ke liye)
             allow_delegation  -> kya ye doosre agent ko kaam de sakta hai
             inject_date       -> aaj ki date prompt mein daal do
             verbose           -> steps print karo

 Run:
     uv run python class_02_agents_tasks/01_agent_attributes.py
=====================================================================
"""

from crewai import Agent

from llm_setup import get_llm

analyst = Agent(
    role="Business Analyst",
    goal="Give practical and low-cost ideas for small businesses",
    backstory="You have helped 100+ small businesses in Lahore grow.",
    llm=get_llm(),
    max_iter=5,               # 5 se zyada dafa nahi sochega
    max_execution_time=120,   # 2 minute ki limit
    max_rpm=10,               # 1 minute mein max 10 LLM calls
    allow_delegation=False,   # akela kaam karega
    inject_date=True,         # aaj ki date pata hogi (season wali ideas ke liye)
    verbose=True,
)

result = analyst.kickoff(
    "Give 3 marketing ideas for an online watch store for this month. "
    "Keep each idea to 1 line."
)
print("\n", result.raw)
