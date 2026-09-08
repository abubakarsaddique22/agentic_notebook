from crewai.flow.flow import Flow, start, listen, router
from crewai import Agent
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import Literal

# load the api keys
load_dotenv()

# define structured state
class AgentState(BaseModel):
    
    product_name: str = Field(description="name of the product", default="")
    product_feedback: str = Field(description="Feedback of the Product", default="")
    feedback_sentiment: Literal["positive", "negative"] | None = Field(description="Sentiment of product feedback", default=None)
    feedback_response: str = Field(description="Response based on the feedback sentiment", default="")


# define the structured output
class ProductFeedback(BaseModel):
    
    feedback: str = Field(description="Feedback of the product in 1 to 2 lines")
    sentiment: Literal["positive", "negative"] = Field(description="Sentiment of the feedback. Can be either positive or negative")
    
# define the flow
class MyAgentRouterFlow(Flow[AgentState]):
    
    # define the response agent
    def response_agent(self, feedback: str, sentiment: Literal["positive", "negative"]) -> Agent:
        return Agent(
            role="Expert Customer Support Assistant",
            goal=f"based on the product feedback: {feedback} and sentiment: {sentiment}, give a response to the customer in a few lines only",
            backstory="You are an expert in handling customer queries and feedbacks and you can design proper responses based on the sentiment of the feedback and the language used inside the feedback"
        )
    
    # define the start node
    @start()
    def get_product_name(self) -> str:
        product_name = self.state.product_name
        return product_name
    
    # define the node that generates feedback and sentiment
    @listen(get_product_name)
    def generate_feedback_sentiment(self, product_name) -> dict[str, str]:
        # define the agent for feedback and sentiment
        feedback_agent = Agent(
            role=f"Expert on feedback and feedback sentiment for product: {product_name}",
            goal=f"Based on the product_name: {product_name}, generate a 2 line feedback and the sentiment of the feedback. The feedback can be either positive or negative",
            backstory=f"You are an expert in giving feedback for {product_name} and also recognizing its sentiment. Your feedback reflects the styling of a real life customer of the product: {product_name}"
        )
        
        # define the prompt
        feedback_prompt = f"Based on the product: {product_name}, generate a customer like feedback and its sentiment. The whole process should be random. You can wither give a positive or a negative feedback"
        
        # agent output
        agent_output = feedback_agent.kickoff(feedback_prompt, response_format=ProductFeedback).pydantic
        
        # save the agent output in state
        self.state.product_feedback = agent_output.feedback
        self.state.feedback_sentiment = agent_output.sentiment
        
        return agent_output.model_dump()
    
    # define the router node
    @router(generate_feedback_sentiment)
    def sentiment_routing(self) -> Literal["positive", "negative"]:
        if self.state.feedback_sentiment == "positive":
            return "positive"
        elif self.state.feedback_sentiment == "negative":
            return "negative"
        
    # define the positive path
    @listen("positive")
    def positive_response(self) -> str:
        feedback = self.state.product_feedback
        sentiment = self.state.feedback_sentiment
        agent = self.response_agent(feedback, sentiment)
        prompt=f"Based on the feedback of the product and its sentiment, give a proper response to the customer in as much few lines as possible\nfeedback:{feedback} sentiment:{sentiment}"
        agent_response = agent.kickoff(prompt).raw
        # add the response to state
        self.state.feedback_response = agent_response
        return agent_response
    
    # define the negative path
    @listen("negative")
    def negative_response(self) -> str:
        feedback = self.state.product_feedback
        sentiment = self.state.feedback_sentiment
        agent = self.response_agent(feedback, sentiment)
        prompt=f"Based on the feedback of the product and its sentiment, give a proper response to the customer in as much few lines as possible\nfeedback:{feedback} sentiment:{sentiment}"
        agent_response = agent.kickoff(prompt).raw
        # add the response to state
        self.state.feedback_response = agent_response
        return agent_response
    
if __name__ == "__main__":
    
    flow = MyAgentRouterFlow()
    
    # execute the flow
    flow_output = flow.kickoff({
        "product_name": "Gaming Console"
    })
    
    print("Flow Output: ", flow_output)
    print(flow.state.model_dump())