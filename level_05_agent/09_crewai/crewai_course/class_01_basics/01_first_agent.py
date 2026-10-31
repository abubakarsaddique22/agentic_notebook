"""
=====================================================================
 CLASS 01 | FILE 01: first_agent.py
=====================================================================
 CONCEPT: Agent (akela agent, bina Crew ke)
 Kya hai : Agent ek AI "employee" hai. Isay 3 cheezein batani hoti hain:
             role      -> ye kaun hai   (e.g. "Python Teacher")
             goal      -> isay kya hasil karna hai
             backstory -> iski personality / experience
           In teeno se CrewAI agent ka "system prompt" banata hai.
 Kyun    : Sab se simple cheez — ek agent ko seedha sawal do aur jawab lo.
           Iske liye agent.kickoff("sawal") use hota hai.

 Run (course folder se):
     uv run python class_01_basics/01_first_agent.py
=====================================================================
"""

from crewai import Agent

from llm_setup import get_llm

# 1) Agent banao
teacher = Agent(
    role="Friendly Python Teacher",
    goal="Explain Python concepts to beginners in simple words",
    backstory="You have been teaching Python to students for 10 years and always give short examples.",
    llm=get_llm(),
    verbose=True,  # True = terminal mein agent ki soch (steps) dikhegi
)

# 2) Agent ko seedha kaam do
result = teacher.kickoff("What is the difference between a list and a tuple? Answer in 3 lines.")

# 3) Jawab print karo
print("\n========== FINAL ANSWER ==========")
print(result.raw)  # .raw = plain text jawab
