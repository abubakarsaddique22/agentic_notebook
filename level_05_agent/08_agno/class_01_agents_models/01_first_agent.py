"""
=====================================================================
 CLASS 01 | FILE 01: first_agent.py
=====================================================================
 CONCEPT: Agent + Model
 Kya hai : Agno mein Agent = Model (LLM ka dimaag) + instructions +
           (baad mein) tools, memory, knowledge.
           Sab se simple agent sirf ek model se banta hai.
   print_response() -> jawab terminal mein sundar box mein print
   stream=True      -> jawab word-by-word aata hai (ChatGPT jaisa)
   markdown=True    -> headings / bullets theek dikhenge

 Run (course folder se):
     uv run python class_01_agents_models/01_first_agent.py
=====================================================================
"""

from agno.agent import Agent

from llm_setup import get_model

agent = Agent(
    name="first_agent",
    model=get_model(),
    markdown=True,
)

agent.print_response("Hi! What is the difference between an agent and a chatbot? Answer in 3 lines.", stream=True)
