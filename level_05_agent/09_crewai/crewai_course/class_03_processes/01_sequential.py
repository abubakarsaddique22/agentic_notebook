"""
=====================================================================
 CLASS 03 | FILE 01: sequential.py
=====================================================================
 CONCEPT: Process.sequential  (line mein kaam — assembly line)
 Kya hai : Tasks list ke order mein ek ke baad ek chalte hain.
           Task 1 khatam -> uska output Task 2 ko -> Task 2 khatam -> ...
 Kab use karein: Jab kaam ka order fix ho (research -> write -> edit).
           Ye DEFAULT process hai.

   [Task 1: Outline] --> [Task 2: Draft] --> [Task 3: Edit] --> Result

 Run:
     uv run python class_03_processes/01_sequential.py
=====================================================================
"""

from crewai import Agent, Task, Crew, Process

from llm_setup import get_llm

llm = get_llm()

planner = Agent(
    role="Content Planner", 
    goal="Create the article outline",
    backstory="You create a clear structure for every article.", 
    llm=llm
    )

writer = Agent(
    role="Content Writer", 
    goal="Write the article from the outline",
    backstory="You write in a simple and engaging way.", 
    llm=llm
    )

editor = Agent(
    role="Editor", 
    goal="Make the article short and error-free",
    backstory="You cut every unnecessary word.", 
    llm=llm
    )

topic = "Why Git is important for beginners"

outline = Task(
    description=f"Create a 4-point outline for '{topic}'.",
    expected_output="4 numbered headings", 
    agent=planner
    )

draft = Task(
    description="Write a 150-word article from the outline.",
    expected_output="A 150-word article", 
    agent=writer
)
edit = Task(
    description="Edit the article: cut it down to 100 words and fix the grammar.",
    expected_output="Final 100-word article", 
    agent=editor
)

crew = Crew(
    agents=[planner, writer, editor],
    tasks=[outline, draft, edit],
    process=Process.sequential,   # <-- line mein chalo (default bhi yahi hai)
    verbose=True,
)

print("\n===== FINAL =====\n", crew.kickoff().raw)
