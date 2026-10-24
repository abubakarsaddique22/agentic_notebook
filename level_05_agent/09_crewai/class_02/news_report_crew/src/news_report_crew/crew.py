from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List
from pydantic import BaseModel , Field
from crewai_tools import SerperDevTool

# define tool for web serach 
web_search_tool = SerperDevTool()


# define structure output 

# ✅ Output Models (Correct)
class NewsReport(BaseModel):
    headline: str = Field(description="Headline for the news")
    url: str = Field(description="URL for the news web page")
    news_summary: str = Field(description="Summary of the news")
    news_agency_name: str = Field(description="Name of the news agency that published the news")


class NewsReports(BaseModel):
    reports: List[NewsReport] = Field(description="List of top 5 news reports")

    
@CrewBase
class NewsReportCrew():
    """NewsReportCrew crew"""

    agents: List[BaseAgent]
    tasks: List[Task]

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    @agent
    def news_reporter(self) -> Agent:
        return Agent(
            config=self.agents_config['news_reporter'], 
            verbose =True ,
            tools=[web_search_tool]
        )

   
    @task
    def reporting_task(self) -> Task:
        return Task(
            config=self.tasks_config['reporting_task'],
            output_file = 'news.json',
            output_json=NewsReports
        )

    
    
    @crew
    def crew(self) -> Crew:
        """Creates the NewsReportCrew crew"""

        return Crew(
            agents=self.agents, 
            tasks=self.tasks, 
            process=Process.sequential,
            verbose=True
        )
