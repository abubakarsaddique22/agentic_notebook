"""
=====================================================================
 CLASS 08 | FILE 06: crew_inside_flow.py
=====================================================================
 CONCEPT: Crew inside Flow (CrewAI ka production pattern)
 Kya hai : Flow poore workflow ka "boss" hai (order, branching, state).
           Jis step mein team wala, sochne wala kaam ho — wahan ek
           poori Crew chala do. Crew ka output wapas flow state mein.

   get_inputs ──▶ research_crew (Crew) ──▶ quality_check (router)
                                              │pass        │fail
                                              ▼            ▼
                                         save_report   flag_for_human

 Run:
     uv run python class_08_flows_advanced/06_crew_inside_flow.py
=====================================================================
"""

from pathlib import Path

from pydantic import BaseModel

from crewai import Agent, Task, Crew
from crewai.flow import Flow, start, listen, router

from llm_setup import get_llm

llm = get_llm()


def build_market_crew() -> Crew:
    researcher = Agent(role="Market Researcher", goal="Find market trends",
                       backstory="You know the Pakistani e-commerce market.", llm=llm)
    strategist = Agent(role="Strategist", goal="Turn research into an action plan",
                       backstory="You get big results on a small budget.", llm=llm)
    t1 = Task(description="List 3 Pakistan market trends for '{product}'.",
              expected_output="3 bullet points", agent=researcher)
    t2 = Task(description="Create a 3-step marketing plan from the trends.",
              expected_output="3 numbered steps", agent=strategist)
    return Crew(agents=[researcher, strategist], tasks=[t1, t2])


class ReportState(BaseModel):
    product: str = ""
    report: str = ""


class MarketFlow(Flow[ReportState]):

    @start()
    def get_inputs(self):
        print("Product:", self.state.product)

    @listen(get_inputs)
    def research_crew(self):
        result = build_market_crew().kickoff(inputs={"product": self.state.product})
        self.state.report = result.raw

    @router(research_crew)
    def quality_check(self):
        return "pass" if len(self.state.report.split()) >= 15 else "fail"

    @listen("pass")
    def save_report(self):
        out = Path("outputs") / "market_plan.md"
        out.parent.mkdir(exist_ok=True)
        out.write_text(self.state.report, encoding="utf-8")
        return f"Report saved: {out}"

    @listen("fail")
    def flag_for_human(self):
        return "Report is too short — sent to a human for review."


flow = MarketFlow()
print("\n", flow.kickoff(inputs={"product": "smart watches"}))
print("\nREPORT:\n", flow.state.report)
