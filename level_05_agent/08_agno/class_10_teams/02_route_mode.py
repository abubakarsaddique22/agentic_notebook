"""
=====================================================================
 CLASS 10 | FILE 02: route_mode.py
=====================================================================
 CONCEPT: Team — ROUTE mode (receptionist pattern)
 Kya hai : Leader sirf decide karta hai ke sawal KIS member ka hai,
           usay bhej deta hai, aur member ka jawab SEEDHA user ko jata
           hai (leader dobara nahi likhta).
 Kyun    : Tez aur sasta (leader ki ek hi choti call). Customer
           support, language routing, department routing ke liye best.

                    ┌─▶ Urdu Agent
   sawal ─▶ Leader ─┼─▶ English Agent
                    └─▶ Arabic Agent

 Run:
     uv run python class_10_teams/02_route_mode.py
=====================================================================
"""

from agno.agent import Agent
from agno.team import Team, TeamMode

from llm_setup import get_model

urdu_agent = Agent(name="Urdu Agent", role="Answers questions asked in Roman Urdu / Urdu",
                   model=get_model(), instructions=["Always answer in Roman Urdu"])
english_agent = Agent(name="English Agent", role="Answers questions asked in English",
                      model=get_model(), instructions=["Always answer in English"])
arabic_agent = Agent(name="Arabic Agent", role="Answers questions asked in Arabic",
                     model=get_model(), instructions=["Always answer in Arabic"])

support_router = Team(
    name="Language Router",
    mode=TeamMode.route,               # <-- route mode
    model=get_model(),
    members=[urdu_agent, english_agent, arabic_agent],
    instructions=["Detect the user's language and route to the agent for that language"],
    markdown=True,
)

support_router.print_response("Bhai meri watch ki delivery kab tak hogi?")
support_router.print_response("What is your return policy?")
