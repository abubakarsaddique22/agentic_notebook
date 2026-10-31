"""
=====================================================================
 CLASS 04 | FILE 01: builtin_tools.py
=====================================================================
 CONCEPT: Tools (built-in tools from crewai_tools)
 Kya hai : LLM sirf "soch" sakta hai. Tool usay "haath" deta hai —
           file parhna, web search karna, file likhna, etc.
           Agent khud faisla karta hai ke kab kaunsa tool use karna hai.
 Kahan se: crewai_tools package mein 100+ ready-made tools hain.

 Is file mein tools:
   DirectoryReadTool -> folder mein kaunsi files hain
   FileReadTool      -> file ka text parhna
   FileWriterTool    -> nayi file likhna
   SerperDevTool     -> Google search (sirf agar SERPER_API_KEY ho)

 Run:
     uv run python class_04_tools/01_builtin_tools.py
=====================================================================
"""

import os
from pathlib import Path

from crewai import Agent, Task, Crew
from crewai_tools import DirectoryReadTool, FileReadTool, FileWriterTool, SerperDevTool

from llm_setup import get_llm

DATA_DIR = Path(__file__).parent / "sample_data"

# ---------- Tools banao ----------
dir_tool = DirectoryReadTool(directory=str(DATA_DIR))
read_tool = FileReadTool()
write_tool = FileWriterTool()

tools = [dir_tool, read_tool, write_tool]

# Web search sirf tab jab key ho (optional)
if os.getenv("SERPER_API_KEY"):
    tools.append(SerperDevTool(n_results=3))
    print("Web search tool ON")

# ---------- Agent ko tools do ----------
assistant = Agent(
    role="Store Assistant",
    goal="Read the store files and give correct answers",
    backstory="You know the store data well and never guess.",
    tools=tools,          # <-- yahan tools diye
    llm=get_llm(),
    verbose=True,
)

task = Task(
    description=(
        f"List and read the files in the '{DATA_DIR}' folder. Then tell me: "
        "which watches are out of stock and what is the return policy? "
        "Also write the answer to the file 'outputs/stock_report.txt' "
        "(FileWriterTool: filename='stock_report.txt', directory='outputs')."
    ),
    expected_output="List of out-of-stock watches + the return policy (2-4 lines).",
    agent=assistant,
)

result = Crew(agents=[assistant], tasks=[task]).kickoff()
print("\n===== ANSWER =====\n", result.raw)
