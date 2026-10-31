"""
=====================================================================
 CLASS 02 | FILE 03: task_context.py
=====================================================================
 CONCEPT: Task Context (ek task ka output doosre task ko dena)
 Kya hai : context=[task_a, task_b] likhne se ye task un dono ka
           output "parh" ke kaam karta hai.
 Kyun    : By default sequential crew mein sirf PICHLA task ka output
           aage jata hai. Agar Task 3 ko Task 1 aur Task 2 dono chahiye,
           to context use karo.

   Task 1 (pros)  ----\
                       >---- Task 3 (final decision)
   Task 2 (cons)  ----/

 Run:
     uv run python class_02_agents_tasks/03_task_context.py
=====================================================================
"""

from crewai import Agent, Task, Crew

from llm_setup import get_llm

llm = get_llm()

optimist = Agent(
    role="Optimist", 
    goal="Find the benefits of every idea",
    backstory="You always look at the positive side.", 
    llm=llm
    )

critic = Agent(
    role="Critic", 
    goal="Find the downsides of every idea",
    backstory="You spot the risk in every plan.", 
    llm=llm
)
judge = Agent(
    role="Judge", 
    goal="Make a decision after weighing pros and cons",
    backstory="You give balanced and direct decisions.", 
    llm=llm
)

idea = "A student starting freelancing alongside their studies"

pros_task = Task(
    description=f"Write 3 benefits of this idea: {idea}",
    expected_output="3 bullet points", 
    agent=optimist
)

cons_task = Task(
    description=f"Write 3 downsides of this idea: {idea}",
    expected_output="3 bullet points", 
    agent=critic
)

decision_task = Task(
    description="Read both the pros and cons and give a final recommendation.",
    expected_output="A final decision in 2-3 lines.",
    agent=judge,
    context=[pros_task, cons_task],   # <-- dono tasks ka output milega
)

crew = Crew(agents=[optimist, critic, judge],
            tasks=[pros_task, cons_task, decision_task])

result = crew.kickoff()
print("\n===== FINAL DECISION =====\n", result.raw)
