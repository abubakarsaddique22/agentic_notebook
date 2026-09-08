from crewai import Agent, Crew, Process, Task , TaskOutput, LLM
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List, Any 

# define the crew base class --> class name should be similar to project name
@CrewBase
class ReportSummarizationCrew():
    """ReportSummarizationCrew crew"""

    # define the datatypes of agents and tasks
    agents: List[BaseAgent]
    tasks: List[Task]
   
    # added paths to yaml config files
    agent_config = "config/agents.yaml"
    task_config = 'config/tasks.yaml'

  # guardrail for report summarization task
    def validate_word_count_for_summary(self, result: TaskOutput) -> tuple[bool, Any]:
        try:
            # define the word limit
            word_limit = 400
            # extract the string output from task output
            result: str = result.raw.strip()
            # tokenize the output and calculate word count
            word_count: int = len(result.split(" "))
            # check whether word count exceeds word limit
            if word_count > word_limit:
                return (False, "Summary exceeds the word count of 300 words, reduce the length to 300 words")
            return (True, result)
        except Exception as e:
            return (False, f"Unexpected error occured  Error: {str(e)}")

  
  
    # ollama_llm = LLM(
    #     model="ollama/llama3.1",
    #     base_url="http://localhost:11434"
    # )


   # define my two agent 
    @agent
    def report_generator(self) -> Agent:
        return Agent(
            config=self.agents_config['report_generator'], 
            # llm=self.ollama_llm,
            verbose=True
        )

    @agent
    def report_summarizer(self) -> Agent:
        return Agent(
            config=self.agents_config['report_summarizer'],
            # llm=self.ollama_llm,
            verbose=True
        )
    
    # define my two tasks
    # always define your tasks based on the order of execution
    @task
    def report_generation_task(self) -> Task:
        return Task(
            config=self.tasks_config['report_generation_task'],
            output_file="reports/report_new.md"
        )

    @task
    def report_summarization_task(self) -> Task:
        return Task(
            config=self.tasks_config['report_summarization_task'],
            output_file='reports/report_summary.md',
            guardrail=self.validate_word_count_for_summary,
            guardrail_max_retries=3
        )



    @crew
    def crew(self) -> Crew:
        """Creates the ReportSummarizationCrew crew"""
        return Crew(
            agents=self.agents, 
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
