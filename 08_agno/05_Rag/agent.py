from agno.agent import Agent
from agno.models.openrouter import OpenRouter  # Use the native OpenRouter class
from knowledge_base import knowledge_base
from dotenv import load_dotenv
import os

# 1. Load the api keys
load_dotenv()

llm = OpenRouter(id="gpt-4o-mini")

# 3. Create the agent
agent = Agent(
    model=llm,
    knowledge=knowledge_base,
    name="Knowledge_Agent",
    search_knowledge=True,
    instructions=[
        "you are a helpful assistant",
        "whenever asked about transformer model, use the knowledge base to get the context",
        "try not to hallucinate while responding",
        "if you don't know the answer to a particular query just say I dont know"
    ],
    stream=True,
    markdown=True
)

agent.print_response("Can you tell me what hardware was used for training the transformer model?")
agent.print_response('Encoder and Decoder Stacks')
agent.print_response('which city is capital pakistan')
