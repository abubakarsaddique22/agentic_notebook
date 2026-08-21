from crewai.flow.flow import Flow, start, listen
from crewai import Agent
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# load the api keys to env
load_dotenv()

# define class for structured output
class CityName(BaseModel):
    
    city_name: str = Field(description="Name of the city generated")
    country: str = Field(description="Name of the country where the city belongs to")


# create the agent flow
class MyAgentFlow(Flow):
    
    # define the start node
    @start()
    def generate_city_name(self) -> dict[str, str]:
        # define agent that gives city name and country name
        city_agent = Agent(
            role="Expert in City Names and Country Names of the world",
            goal="Generate a real world city name and also its corresponding name of the country and the output is different everytime",
            backstory="You are an expert in Geography and World Map. You know a lot about cities in the world and the country where the city belongs to"
        )
        # define the prompt
        prompt = "Generate a real world city name and its corresponding country name as well"
        # get the agent output --> pydantic class
        agent_output = city_agent.kickoff(messages=prompt,
                                          response_format=CityName)
        # return the agent output as a dict
        print(f"City Name Output: {agent_output.pydantic.model_dump()}")
        return agent_output.pydantic.model_dump()
    
    # define the second node
    @listen(generate_city_name)
    def generate_fact(self, node_output) -> str:
        city_name = node_output["city_name"]
        country_name = node_output["country"]
        # define the agent that gives the fact about city
        fact_agent = Agent(
            role="Expert in Fun Fact Generation for Cities around the world",
            goal=f"Generate a fun fact about the city: {city_name}. Also include the country name: {country_name} in the output",
            backstory=f"You are an expert in generating fun facts about city: {city_name}. The facts are fun to read and novel"
        )
        # define the input prompt
        prompt = f"Generate a fun fact about {city_name} and the fact should be fun to read. Also include the name of the country: {country_name} in the output"
        # execute the fact agent
        fact = fact_agent.kickoff(prompt)
        return fact.raw
    
if __name__ == "__main__":
    # create the flow
    flow = MyAgentFlow()
    
    # execute the flow
    result = flow.kickoff()
    
    # plot the flow
    flow.plot("city_agent_flow.html")
    
    # print the result
    print(f"Flow Output:\n{result}")