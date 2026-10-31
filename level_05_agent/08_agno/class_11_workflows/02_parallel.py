"""
=====================================================================
 CLASS 11 | FILE 02: parallel.py
=====================================================================
 CONCEPT: Parallel steps (ek saath chalana)
 Kya hai : Parallel(step_a, step_b) -> dono steps EK SAATH chalte hain.
           Agla step dono ke outputs le sakta hai:
             step_input.get_step_content("Parallel ka naam")
             -> {"Step A naam": "...", "Step B naam": "..."}
           ya seedha step_input.previous_step_content.
 Kyun    : Alag sources se data lana (web + news + database) — time
           aadha ho jata hai.

   ┌─ HackerNews Search ─┐
   ├─ Web Search ────────┼──▶ Report Writer
   └─ Store Data (py) ───┘

 Run:
     uv run python class_11_workflows/02_parallel.py
=====================================================================
"""

from agno.agent import Agent
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.hackernews import HackerNewsTools
from agno.workflow import Parallel, Step, StepInput, StepOutput, Workflow

from llm_setup import get_model

hn_agent = Agent(name="HN Agent", model=get_model(), tools=[HackerNewsTools()],
                 instructions=["Get the top 2 Hacker News stories on the topic", "Heading: Source: HackerNews"])
web_agent = Agent(name="Web Agent", model=get_model(), tools=[DuckDuckGoTools()],
                  instructions=["Get the 2 latest web news stories on the topic", "Heading: Source: Web"])
report_agent = Agent(name="Report Writer", model=get_model(), markdown=True,
                     instructions=["Combine all sources into one clean report",
                                   "Mention the source name with every point"])


def internal_data(step_input: StepInput) -> StepOutput:
    return StepOutput(content="Source: Store DB — sales of 'AI' related gadgets are up 20% this month.")


workflow = Workflow(
    name="Research Report",
    steps=[
        Parallel(
            Step(name="HackerNews Search", agent=hn_agent),
            Step(name="Web Search", agent=web_agent),
            Step(name="Store Data", executor=internal_data),
            name="Gather Data",
        ),
        Step(name="Write Report", agent=report_agent),
    ],
)

workflow.print_response("Topic: AI agents", stream=True, markdown=True)
