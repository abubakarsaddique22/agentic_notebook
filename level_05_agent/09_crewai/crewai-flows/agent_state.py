from crewai.flow.flow import Flow, start, listen
from crewai import Agent
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import Literal

# load the api keys into the env
load_dotenv()

class AgentState(BaseModel):
    
    topic: str = Field(description="Topic given as input", default="")
    description: str = Field(description="1 paragragh description about the topic", default="")
    topic_category: Literal["Technical", "Non-Technical"] | None = Field(description="Category of topic as technical or non-technical",default=None)


class AgentOutput(BaseModel):
    
    topic_description: str = Field(description="One paragraph description about the topic")
    category: Literal["Technical", "Non-Technical"] = Field(description="Category of the input topic as technical or non-technical")
    

# define the flow
class AgenticStateFlow(Flow[AgentState]):
    
    # define the start node
    @start()
    def get_topic(self) -> str:
        topic = self.state.topic
        return topic
    
    # generate description and category
    @listen(get_topic)
    def gen_description(self, topic) -> dict[str, str]:
        # build the agent
        agent = Agent(
            role=f"Expert in Describing {topic}",
            goal=f"Your goal is to give a one paragraph description about the topic and also categorize the topic as technical or non-technical",
            backstory=f"You are an expert in the field of {topic}. You can summarize the {topic} and give description about it"
        )
        
        # build the prompt
        prompt = f"Generate a short one paragraph descriptioon about the topic: {topic}. Also categorize the topic as technical or non-technical"
        
        # execute the agent
        response = agent.kickoff(prompt, response_format=AgentOutput)
        
        # update the agent state
        self.state.description = response.pydantic.topic_description
        self.state.topic_category = response.pydantic.category
        
        # return the state as dictionary
        return self.state.model_dump()
    

if __name__ == "__main__":
    # create the flow
    flow = AgenticStateFlow()
    
    # execute the flow
    flow_output = flow.kickoff({
        "topic": "AI Agents in Coding"
    })
    
    print(f"Final State: {flow_output}")