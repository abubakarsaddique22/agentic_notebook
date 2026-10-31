"""
=====================================================================
 CLASS 10 | FILE 04: tasks_mode.py
=====================================================================
 CONCEPT: Team — TASKS mode (autonomous task list)
 Kya hai : Leader bara goal le ke usay chhote TASKS ki list mein
           todta hai, har task kisi member ko deta hai, results check
           karta hai aur jab tak SAARE tasks complete na hon, loop
           chalata rehta hai. (Project manager + to-do list)
 Kyun    : Bara, multi-step kaam jahan steps pehle se fix nahi
           (e.g. "launch plan banao").
 Note    : Sab se zyada LLM calls — free API pe rate limit aa sakti hai.

 Run:
     uv run python class_10_teams/04_tasks_mode.py
=====================================================================
"""

from agno.agent import Agent
from agno.team import Team, TeamMode

from llm_setup import get_model

market_analyst = Agent(name="Market Analyst", role="Analyzes target customers and competitors",
                       model=get_model())
marketer = Agent(name="Marketer", role="Writes social media posts and ad copy", model=get_model())
planner = Agent(name="Planner", role="Creates the budget and timeline", model=get_model())

launch_team = Team(
    name="Launch Team",
    mode=TeamMode.tasks,               # <-- leader task list banayega
    model=get_model(),
    members=[market_analyst, marketer, planner],
    instructions=["Break the goal into 3-5 tasks", "Check the result of every task"],
    markdown=True,
)

launch_team.print_response(
    "Create a 2-week launch plan for a new analog watch brand in Lahore. Budget 50,000 PKR."
)
