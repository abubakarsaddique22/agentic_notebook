"""
=====================================================================
 CLASS 09 | watch_review_crew/crew.py
=====================================================================
 CONCEPT: @CrewBase (YAML wala project structure — official style)
 Kya hai : Ye wahi structure hai jo `crewai create crew my_crew`
           command banati hai. Decorators:
             @CrewBase      -> class ko CrewAI project banata hai,
                               config/agents.yaml + config/tasks.yaml
                               khud load karta hai
             @agent         -> function jo Agent return kare
             @task          -> function jo Task return kare
             @crew          -> final Crew banata hai
             @before_kickoff-> crew start hone se PEHLE inputs badlo
             @after_kickoff -> crew khatam hone ke BAAD result badlo
           self.agents / self.tasks khud bhar jate hain (decorators se),
           tasks usi ORDER mein jitne functions likhe hain.
=====================================================================
"""

from datetime import datetime

from crewai import Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, crew, task, before_kickoff, after_kickoff

from llm_setup import get_llm


@CrewBase
class WatchReviewCrew:
    """Watch review crew"""

    agents_config = "config/agents.yaml"    # path is file ke folder se relative
    tasks_config = "config/tasks.yaml"

    agents: list[BaseAgent]
    tasks: list[Task]

    # ---------- Hooks ----------
    @before_kickoff
    def add_defaults(self, inputs):
        inputs.setdefault("price", "5000")
        print(f"[before_kickoff] inputs: {inputs}")
        return inputs

    @after_kickoff
    def stamp_result(self, result):
        result.raw += f"\n\n_Generated on {datetime.now():%d %b %Y}_"
        return result

    # ---------- Agents ----------
    @agent
    def product_analyst(self) -> Agent:
        return Agent(config=self.agents_config["product_analyst"], llm=get_llm())

    @agent
    def review_writer(self) -> Agent:
        return Agent(config=self.agents_config["review_writer"], llm=get_llm())

    # ---------- Tasks ----------
    @task
    def analysis_task(self) -> Task:
        return Task(config=self.tasks_config["analysis_task"])

    @task
    def review_task(self) -> Task:
        return Task(config=self.tasks_config["review_task"], output_file="outputs/review.md")

    # ---------- Crew ----------
    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
