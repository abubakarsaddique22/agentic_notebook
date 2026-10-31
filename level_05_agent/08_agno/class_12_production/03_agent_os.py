"""
=====================================================================
 CLASS 12 | FILE 03: agent_os.py
=====================================================================
 CONCEPT: AgentOS (agents ko API / web app bana ke serve karna)
 Kya hai : Ab tak sab terminal mein tha. Production mein agent ek
           SERVER hona chahiye jise website, WhatsApp bot, mobile app
           call kar sakein. AgentOS:
             - agents / teams / workflows ko FastAPI app bana deta hai
             - har agent ke ready-made API endpoints (chat, sessions,
               memories, knowledge)
             - Agno ka web UI (os.agno.com) is server se connect ho ke
               chat, sessions, memory sab dikhata hai
 Steps   :
   1) ye file chalao -> server http://localhost:7777 pe chalega
   2) browser: http://localhost:7777/docs  -> saari APIs (Swagger)
   3) optional: https://os.agno.com pe login -> "Add OS" -> localhost:7777
   4) doosri cmd window se agent ko API call (Windows 10+ mein curl hai):
      curl -X POST http://localhost:7777/agents/support-agent/runs -F "message=When will my delivery arrive?" -F "stream=false"
   Band karna: Ctrl + C

 Run:
     uv run python class_12_production/03_agent_os.py
=====================================================================
"""

from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.os import AgentOS
from agno.team import Team

from llm_setup import get_model

db = SqliteDb(db_file="tmp/agent_os.db")

support_agent = Agent(
    id="support-agent",
    name="Support Agent",
    model=get_model(),
    db=db,
    add_history_to_context=True,
    update_memory_on_run=True,
    instructions=["You are the support agent of the TimeHouse watch store"],
    markdown=True,
)

sales_agent = Agent(
    id="sales-agent",
    name="Sales Agent",
    model=get_model(),
    db=db,
    instructions=["Suggest watches to the customer based on their budget"],
    markdown=True,
)

store_team = Team(
    id="store-team",
    name="Store Team",
    model=get_model(),
    members=[support_agent, sales_agent],
    db=db,
)

agent_os = AgentOS(
    name="TimeHouse OS",
    agents=[support_agent, sales_agent],
    teams=[store_team],
)

app = agent_os.get_app()      # ye ek normal FastAPI app hai

if __name__ == "__main__":
    agent_os.serve(app=app, port=7777)
