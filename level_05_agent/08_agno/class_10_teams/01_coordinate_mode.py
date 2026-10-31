"""
=====================================================================
 CLASS 10 | FILE 01: coordinate_mode.py
=====================================================================
 CONCEPT: Team (multi-agent) — COORDINATE mode (default)
 Kya hai : Team = kayi specialist agents + ek LEADER (team ka model).
           Coordinate mode mein leader:
             1) sawal parhta hai
             2) kaam ko hisson mein baant ke sahi members ko deta hai
             3) sab ke jawab jama karke FINAL jawab khud likhta hai
           Member agent ka `role` bohot zaroori hai — leader isi se
           decide karta hai kis ko kaam dena hai.

            [ Leader ]
           /    |     \
     Researcher Writer  SEO

 Run:
     uv run python class_10_teams/01_coordinate_mode.py
=====================================================================
"""

from agno.agent import Agent
from agno.team import Team, TeamMode
from agno.tools.duckduckgo import DuckDuckGoTools

from llm_setup import get_model

researcher = Agent(
    name="Researcher",
    role="Finds the latest facts from the web",
    model=get_model(),
    tools=[DuckDuckGoTools()],
)

writer = Agent(
    name="Writer",
    role="Writes an easy and engaging blog post from the facts",
    model=get_model(),
)

seo_expert = Agent(
    name="SEO Expert",
    role="Suggests a title and 5 SEO keywords",
    model=get_model(),
)

content_team = Team(
    name="Content Team",
    mode=TeamMode.coordinate,          # default (likhna zaroori nahi)
    model=get_model(),                 # leader ka dimaag
    members=[researcher, writer, seo_expert],
    instructions=["First get the research done, then the writing, then SEO",
                  "Final answer must include: Title, a 150-word blog, keywords"],
    show_members_responses=True,       # members ke jawab bhi dikhao
    markdown=True,
)

content_team.print_response("Smart watches vs analog watches — which should you buy in 2026?", stream=True)
