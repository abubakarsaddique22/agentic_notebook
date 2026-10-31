"""
=====================================================================
 CLASS 11 | FILE 05: router.py
=====================================================================
 CONCEPT: Router (kayi raston mein se ek chunna)
 Kya hai : Router(choices=[step_a, step_b, ...], selector=fn)
             selector(step_input) -> wo step(s) return karo jo chalne
                                     chahiyein
           Condition = sirf haan/na. Router = kayi options.
 Selector Python rules se ho sakta hai (tez, free) ya andar LLM call
 bhi kar sakte ho.

                     ┌─▶ Tech Research (HackerNews)
   topic ─▶ Router ──┼─▶ Sports Research (Web)
                     └─▶ General Research (Web)  ─▶ Article Writer

 Run:
     uv run python class_11_workflows/05_router.py
=====================================================================
"""

from agno.agent import Agent
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.hackernews import HackerNewsTools
from agno.workflow import Router, Step, StepInput, Workflow

from llm_setup import get_model

tech_step = Step(name="Tech Research", agent=Agent(
    name="Tech Researcher", model=get_model(), tools=[HackerNewsTools()]))
sports_step = Step(name="Sports Research", agent=Agent(
    name="Sports Researcher", model=get_model(), tools=[DuckDuckGoTools()],
    instructions=["Only search for sports news"]))
general_step = Step(name="General Research", agent=Agent(
    name="General Researcher", model=get_model(), tools=[DuckDuckGoTools()]))
writer_step = Step(name="Write Article", agent=Agent(
    name="Article Writer", model=get_model(), markdown=True,
    instructions=["Write an article with headings and bullets from the research"]))

TECH_WORDS = ["ai", "software", "tech", "programming", "computer", "gadget"]
SPORTS_WORDS = ["cricket", "football", "psl", "match", "olympics"]


def pick_route(step_input: StepInput) -> list[Step]:
    topic = (step_input.input or "").lower()
    if any(w in topic for w in TECH_WORDS):
        print("   [router] -> Tech")
        return [tech_step]
    if any(w in topic for w in SPORTS_WORDS):
        print("   [router] -> Sports")
        return [sports_step]
    print("   [router] -> General")
    return [general_step]            # default raasta hamesha rakho


workflow = Workflow(
    name="Smart Research",
    steps=[
        Router(name="Topic Router", choices=[tech_step, sports_step, general_step], selector=pick_route),
        writer_step,
    ],
)

workflow.print_response("Latest PSL 2026 news", markdown=True)
