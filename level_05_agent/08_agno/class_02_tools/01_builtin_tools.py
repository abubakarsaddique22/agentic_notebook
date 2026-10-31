"""
=====================================================================
 CLASS 02 | FILE 01: builtin_tools.py
=====================================================================
 CONCEPT: Tools (built-in toolkits)
 Kya hai : Tool = agent ke "haath". Model khud decide karta hai ke kab
           kaunsa tool chalana hai (function calling).
           Agno mein 100+ ready-made toolkits hain (agno.tools.*):
             DuckDuckGoTools  -> web search (free, key nahi)
             HackerNewsTools  -> tech news (free)
             CalculatorTools  -> sahi math (LLM math mein kamzor hai)
           Har toolkit ke andar kayi functions hote hain.

 Run:
     uv run python class_02_tools/01_builtin_tools.py
=====================================================================
"""

from agno.agent import Agent
from agno.tools.calculator import CalculatorTools
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.hackernews import HackerNewsTools

from llm_setup import get_model

# ---------- 1) Web search agent ----------
search_agent = Agent(
    name="search_agent",
    model=get_model(),
    tools=[DuckDuckGoTools()],
    instructions=["Always search the web for the latest information", "Mention the source names"],
    markdown=True,
)
search_agent.print_response("Give me 2 news stories about AI agents from this week.", stream=True)

# ---------- 2) Ek agent, kayi toolkits ----------
multi_agent = Agent(
    name="multi_tool_agent",
    model=get_model(),
    tools=[CalculatorTools(), HackerNewsTools()],
    instructions=["Always use the calculator for math"],
    markdown=True,
)
multi_agent.print_response("Multiply 4599 by 17, then show the top 2 Hacker News stories.", stream=True)
