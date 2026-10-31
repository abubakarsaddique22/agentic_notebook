"""
=====================================================================
 CLASS 01 | FILE 02: first_crew.py
=====================================================================
 CONCEPT: Agent + Task + Crew  (CrewAI ke 3 basic building blocks)
 Kya hai :
   Agent -> kaam KAUN karega
   Task  -> kaam KYA hai  (description + expected_output)
   Crew  -> team, jo agents aur tasks ko jor ke chalati hai
   kickoff() -> "start!" button. Crew kaam shuru kar deti hai.

 Flow:  Crew.kickoff()  ->  Task 1 (Researcher)  ->  Task 2 (Writer)  ->  Result

 Run:
     uv run python class_01_basics/02_first_crew.py
=====================================================================
"""

from crewai import Agent, Task, Crew

from llm_setup import get_llm

llm = get_llm()

# ---------- AGENTS ----------
researcher = Agent(
    role="Researcher",
    goal="Find the 3 most important facts about any topic",
    backstory="You are a careful researcher who only shares what matters.",
    llm=llm,
)

writer = Agent(
    role="Writer",
    goal="Turn facts into a short, engaging post",
    backstory="You write simple and clear content for social media.",
    llm=llm,
)

# ---------- TASKS ----------
research_task = Task(
    description="Find 3 important facts about the topic 'AI Agents'.",
    expected_output="3 bullet points, one line each.",
    agent=researcher,
)

write_task = Task(
    description="Use the researcher's facts to write an 80-word LinkedIn post.",
    expected_output="An 80-word post with 2 hashtags at the end.",
    agent=writer,
)

# ---------- CREW ----------
crew = Crew(
    agents=[researcher, writer],
    tasks=[research_task, write_task],  # tasks isi order mein chalenge
    verbose=True,
)

result = crew.kickoff()

print("\n========== FINAL OUTPUT ==========")
print(result.raw)                       # aakhri task ka jawab

print("\n========== HAR TASK KA OUTPUT ==========")
for task_output in result.tasks_output:  # har task ka alag output
    print("-", task_output.agent, ":", task_output.raw[:80], "...")

print("\nTokens used:", result.token_usage.total_tokens)
