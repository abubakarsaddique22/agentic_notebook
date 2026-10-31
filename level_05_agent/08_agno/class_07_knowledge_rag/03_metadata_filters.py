"""
=====================================================================
 CLASS 07 | FILE 03: metadata_filters.py
=====================================================================
 CONCEPT: Metadata + Knowledge Filters
 Problem : Ek knowledge base mein alag cheezein hain (Lahore branch ki
           policy, Karachi branch ki policy). Search ghalat branch ka
           document utha sakta hai.
 Hal     : insert(..., metadata={"branch": "lahore"}) -> har document pe
           label lagao. Phir:
             knowledge_filters={"branch": "lahore"} -> sirf ye documents
             enable_agentic_knowledge_filters=True  -> agent sawal se
                                                       khud filter nikale
 Kyun    : Multi-user apps (har customer ka apna data), versions,
           categories — sahi document hi mile.

 Run:
     uv run python class_07_knowledge_rag/03_metadata_filters.py
=====================================================================
"""

from agno.agent import Agent
from agno.knowledge.knowledge import Knowledge
from agno.vectordb.lancedb import LanceDb

from llm_setup import get_model, get_embedder

knowledge = Knowledge(
    name="branch_policies",
    vector_db=LanceDb(uri="tmp/lancedb", table_name="branch_policies", embedder=get_embedder()),
)

knowledge.insert(name="lahore_policy", skip_if_exists=True, metadata={"branch": "lahore"},
                 text_content="Lahore branch: same-day delivery, 7-day returns, timings 11am-10pm.")
knowledge.insert(name="karachi_policy", skip_if_exists=True, metadata={"branch": "karachi"},
                 text_content="Karachi branch: 2-day delivery, 3-day returns, timings 12pm-11pm.")

# ---------- 1) Fixed filter (aap decide karte ho) ----------
lahore_agent = Agent(
    model=get_model(),
    knowledge=knowledge,
    search_knowledge=True,
    knowledge_filters={"branch": "lahore"},     # sirf Lahore documents
    markdown=True,
)
lahore_agent.print_response("How many days is the return policy?")

# ---------- 2) Run ke waqt filter ----------
lahore_agent.print_response("What are the timings?", knowledge_filters={"branch": "karachi"})

# ---------- 3) Agentic filters (agent khud nikale) ----------
smart_agent = Agent(
    model=get_model(),
    knowledge=knowledge,
    search_knowledge=True,
    enable_agentic_knowledge_filters=True,
    markdown=True,
)
smart_agent.print_response("How many days does delivery take at the Karachi branch?")
