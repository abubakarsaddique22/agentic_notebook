"""
=====================================================================
 CLASS 10 | FILE 01: mcp_tools.py
=====================================================================
 CONCEPT: MCP tools ko Agent se jorna (mcps=[...])
 Kya hai : Agent(mcps=[...]) mein MCP server do — CrewAI khud server se
           connect karta hai, uske tools list karta hai aur agent ko de
           deta hai. Aap ko tool ka code likhne ki zaroorat nahi.
 Server ki qismein:
   MCPServerStdio(command, args) -> local program (is file mein)
   MCPServerHTTP(url=...)        -> remote server (internet pe)
   "https://some-server.com/mcp" -> seedha URL string bhi chalta hai

 Run:
     uv run python class_10_production/01_mcp_tools.py
=====================================================================
"""

import sys
from pathlib import Path

from crewai import Agent, Task, Crew
from crewai.mcp import MCPServerStdio

from llm_setup import get_llm

SERVER_FILE = Path(__file__).parent / "watch_mcp_server.py"

store_server = MCPServerStdio(
    command=sys.executable,          # wahi python jo abhi chal raha hai (.venv wala)
    args=[str(SERVER_FILE)],
)

support = Agent(
    role="Order Support Agent",
    goal="Give customers correct answers about order status and categories",
    backstory="You always check with the store system (tools).",
    llm=get_llm(),
    mcps=[store_server],             # <-- MCP server ke saare tools mil gaye
    verbose=True,
)

task = Task(
    description="Customer: 'Where is my order 1002? And which categories do you have?'",
    expected_output="Order status + the list of categories, in a polite tone.",
    agent=support,
)

print("\n===== ANSWER =====\n", Crew(agents=[support], tasks=[task]).kickoff().raw)
