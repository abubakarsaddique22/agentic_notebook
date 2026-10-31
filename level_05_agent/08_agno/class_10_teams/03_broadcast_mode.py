"""
=====================================================================
 CLASS 10 | FILE 03: broadcast_mode.py
=====================================================================
 CONCEPT: Team — BROADCAST mode (sab se ek hi sawal)
 Kya hai : Leader SAME sawal har member ko bhejta hai, phir sab ki
           raaye mila ke final jawab banata hai.
           team.arun() (async) mein members EK SAATH chalte hain.
 Kyun    : Alag nazariye chahiye hon — jaise "panel discussion":
           optimist vs critic vs finance. Ya multiple sources se same
           info verify karni ho.

           ┌─▶ Optimist ──┐
   sawal ──┼─▶ Critic ────┼──▶ Leader: final faisla
           └─▶ Finance ───┘

 Run:
     uv run python class_10_teams/03_broadcast_mode.py
=====================================================================
"""

from agno.agent import Agent
from agno.team import Team, TeamMode

from llm_setup import get_model

optimist = Agent(name="Optimist", role="Explains the benefits of every idea", model=get_model())
critic = Agent(name="Critic", role="Explains the risks and downsides of every idea", model=get_model())
finance = Agent(name="Finance Advisor", role="Gives an opinion based on money and budget", model=get_model())

panel = Team(
    name="Decision Panel",
    mode=TeamMode.broadcast,           # <-- sab ko same sawal
    model=get_model(),
    members=[optimist, critic, finance],
    instructions=["Read all three opinions and give a balanced 3-line decision"],
    show_members_responses=True,
    markdown=True,
)

panel.print_response("Should a student invest 100,000 PKR to start an online watch store?")
