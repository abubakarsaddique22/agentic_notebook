"""
=====================================================================
 CLASS 09 | FILE 04: planning.py
=====================================================================
 CONCEPT: Planning (kaam se pehle plan banana)
 Kya hai : 2 levels:
   1) Crew(planning=True) -> crew start hone se pehle ek "AgentPlanner"
      saare tasks ka step-by-step plan banata hai aur har task mein
      daal deta hai. Agents ko pata hota hai poora plan kya hai.
   2) Agent(planning_config=PlanningConfig(...)) -> agent khud task
      se pehle sochta hai ("reasoning"), plan banata hai, phir kaam.
      reasoning_effort: "low" (tez) / "medium" / "high" (zyada soch)
 Note    : Planning = zyada LLM calls = zyada tokens. Mushkil,
           multi-step kaam ke liye use karo, simple kaam ke liye nahi.

 Run:
     uv run python class_09_yaml_project/04_planning.py
=====================================================================
"""

from crewai import Agent, Task, Crew, PlanningConfig

from llm_setup import get_llm

llm = get_llm()

# ---------- Agent-level planning (reasoning) ----------
planner_agent = Agent(
    role="Launch Planner",
    goal="Create a practical product launch plan",
    backstory="You have handled 20+ online launches.",
    llm=llm,
    planning_config=PlanningConfig(reasoning_effort="low", max_attempts=2),
)

writer = Agent(role="Copywriter", goal="Write the launch announcement from the plan",
               backstory="You write exciting but honest copy.", llm=llm)

plan_task = Task(description="Create a 1-week launch plan for a new watch collection (budget 20,000 PKR).",
                 expected_output="Day-wise plan, 7 lines", agent=planner_agent)
announce_task = Task(description="Write the launch announcement for Day 1 of the plan.",
                     expected_output="A 50-word post", agent=writer)

# ---------- Crew-level planning ----------
crew = Crew(
    agents=[planner_agent, writer],
    tasks=[plan_task, announce_task],
    planning=True,          # <-- crew pehle poora plan banayegi
    planning_llm=llm,       # <-- plan banane wala LLM
    verbose=True,
)

print("\n===== RESULT =====\n", crew.kickoff().raw)
