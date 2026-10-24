# from crewai import Agent, Crew, Process, Task
# from crewai.project import CrewBase, agent, crew, task
# from crewai.agents.agent_builder.base_agent import BaseAgent
# from typing import List
# from crewai.knowledge.source.pdf_knowledge_source import PDFKnowledgeSource



# # define the pdf knowledge source
# research_paper_source = PDFKnowledgeSource(
#     file_paths=["survey_on_icl.pdf"],
#     chunk_size=1500,
#     chunk_overlap=250
# )


# @CrewBase
# class KnowledgeCrew():
#     """KnowledgeCrew crew"""

#     agents: List[BaseAgent]
#     tasks: List[Task]

#     agents_config = 'config/agents.yaml'
#     tasks_config = 'config/tasks.yaml'
#     @agent
#     def research_summarization(self) -> Agent:
#         return Agent(
#             config=self.agents_config['research_summarization'], 
#             verbose=True
#         )

    

  
#     @task
#     def summarization_task(self) -> Task:
#         return Task(
#             config=self.tasks_config['summarization_task'], 
#         )

#     @crew
#     def crew(self) -> Crew:
#         """Creates the KnowledgeCrew crew"""
#         return Crew(
#             agents=self.agents, 
#             tasks=self.tasks, 
#             process=Process.sequential,
#             verbose=True,
#             knowledge_sources=[research_paper_source]
#         )



from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from crewai.knowledge.source.pdf_knowledge_source import PDFKnowledgeSource

# 1. Define the LLM using Gemma 3 (1B is optimized for local memory)
local_llm = LLM(
    model="ollama/gemma3:1b",
    base_url="http://localhost:11434"
)

# 2. Define the PDF knowledge source
research_paper_source = PDFKnowledgeSource(
    file_paths=["survey_on_icl.pdf"],
    chunk_size=1500,
    chunk_overlap=250
)

@CrewBase
class KnowledgeCrew():
    """KnowledgeCrew crew using local Ollama models"""

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    @agent
    def research_summarization(self) -> Agent:
        return Agent(
            config=self.agents_config['research_summarization'],
            llm=local_llm, # Use Gemma 3
            verbose=True
        )

    @task
    def summarization_task(self) -> Task:
        return Task(
            config=self.tasks_config['summarization_task'],
        )

    @crew
    def crew(self) -> Crew:
        """Creates the KnowledgeCrew crew with Snowflake embeddings"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
            knowledge_sources=[research_paper_source],
            # 3. Use Snowflake Arctic Embed for high-efficiency local RAG
            embedder={
                "provider": "ollama",
                "config": {
                    "model": "snowflake-arctic-embed:22m",
                    "base_url": "http://localhost:11434"
                }
            }
        )
