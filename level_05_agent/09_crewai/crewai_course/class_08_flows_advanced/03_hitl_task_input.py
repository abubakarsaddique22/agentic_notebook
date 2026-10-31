"""
=====================================================================
 CLASS 08 | FILE 03: hitl_task_input.py
=====================================================================
 CONCEPT: HITL (Human-in-the-Loop) — Crew Task level
 Kya hai : HITL = AI ke kaam mein insaan ka check / approval.
           Task(human_input=True) dene se:
             1) agent apna jawab banata hai
             2) terminal mein aap se feedback maanga jata hai
             3) aap feedback likho  -> agent jawab improve karta hai
                sirf Enter dabao     -> jawab final
 Kyun    : Email bhejne, post publish karne, refund dene jaise kaam
           se pehle insaan ki approval zaroori hoti hai.

 Run:
     uv run python class_08_flows_advanced/03_hitl_task_input.py
=====================================================================
"""

from crewai import Agent, Task, Crew

from llm_setup import get_llm

writer = Agent(
    role="Email Writer",
    goal="Write professional emails to customers",
    backstory="You write polite and short emails.",
    llm=get_llm(),
)

email_task = Task(
    description="Write an email to customer Bilal saying his order (Classic Steel watch) will be delivered tomorrow.",
    expected_output="A subject line + a 4-5 line email.",
    agent=writer,
    human_input=True,          # <-- HITL: aap se review maanga jayega
)

print(">>> Jab feedback maanga jaye: kuch likho (e.g. 'Urdu mein likho') ya Enter dabao.\n")

result = Crew(agents=[writer], tasks=[email_task]).kickoff()
print("\n===== APPROVED EMAIL =====\n", result.raw)
