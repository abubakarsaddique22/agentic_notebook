"""
=====================================================================
 CLASS 03 | FILE 03: custom_manager.py
=====================================================================
 CONCEPT: Custom Manager Agent + Delegation
 Kya hai : manager_llm ki jagah apna khud ka manager agent bana sakte
           ho (manager_agent=...). Is tarah manager ki personality aur
           rules aap control karte ho.
 Delegation: allow_delegation=True wala agent doosre agents ko kaam
           de sakta hai ya unse sawal pooch sakta hai.
 Rule    : Manager ko agents=[...] list mein NAHI daalte.

 Run:
     uv run python class_03_processes/03_custom_manager.py
=====================================================================
"""

from crewai import Agent, Task, Crew, Process

from llm_setup import get_llm

llm = get_llm()

manager = Agent(
    role="Project Manager",
    goal="Get the best quality work from the team and check the final answer",
    backstory="You are a strict but fair manager. You give every task to the right person.",
    llm=llm,
    allow_delegation=True,   # <-- manager kaam baant sakta hai
)

designer = Agent(
    role="UI Designer",
    goal="Suggest simple app screen ideas",
    backstory="You love minimal design.", 
    llm=llm
    )

marketer = Agent(
    role="Marketer", 
    goal="Write a catchy launch message for the app",
    backstory="You do marketing for Gen-Z.", 
    llm=llm
)

task = Task(
    description="For a 'Daily Water Reminder' app: ideas for 3 screens and 1 launch tweet.",
    expected_output="3 screen ideas (1 line each) + 1 tweet",
)

crew = Crew(
    agents=[designer, marketer],   # manager yahan NAHI
    tasks=[task],
    process=Process.hierarchical,
    manager_agent=manager,         # <-- apna manager
    verbose=True,
)

print("\n===== FINAL =====\n", crew.kickoff().raw)
