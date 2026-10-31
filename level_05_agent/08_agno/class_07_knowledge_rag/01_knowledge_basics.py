"""
=====================================================================
 CLASS 07 | FILE 01: knowledge_basics.py
=====================================================================
 CONCEPT: Knowledge (Agentic RAG)
 Kya hai : Knowledge = agent ki "library". Documents (text, PDF, CSV,
           website) ko:
             1) chhote tukron (chunks) mein kaata jata hai
             2) embedder unhein vectors (numbers) mein badalta hai
             3) vector database (LanceDB) mein save hote hain
           Sawal aane pe relevant tukre dhoond ke model ko diye jate hain.
           Isay RAG (Retrieval Augmented Generation) kehte hain.

   search_knowledge=True -> AGENTIC RAG: agent ko "search_knowledge_base"
                            tool milta hai, khud decide karta hai kab
                            dhoondna hai (default bhi yahi hai).
   knowledge.insert(...) -> document add karo
   skip_if_exists=True   -> dobara chalane pe duplicate na bane

 Run:
     uv run python class_07_knowledge_rag/01_knowledge_basics.py
=====================================================================
"""

from pathlib import Path

from agno.agent import Agent
from agno.knowledge.knowledge import Knowledge
from agno.vectordb.lancedb import LanceDb

from llm_setup import get_model, get_embedder

KNOWLEDGE_DIR = Path(__file__).parent / "knowledge"

# 1) Vector database (local folder mein)
vector_db = LanceDb(
    uri="tmp/lancedb",
    table_name="store_docs",
    embedder=get_embedder(),
)

# 2) Knowledge base
knowledge = Knowledge(
    name="store_knowledge",
    description="TimeHouse watch store policies and products",
    vector_db=vector_db,
)

# 3) Documents add karo (text, file, CSV)
knowledge.insert(name="about", text_content="TimeHouse is an online watch store started in Lahore in 2024.",
                 skip_if_exists=True)
knowledge.insert(name="policy", path=str(KNOWLEDGE_DIR / "store_policy.txt"), skip_if_exists=True)
knowledge.insert(name="products", path=str(KNOWLEDGE_DIR / "products.csv"), skip_if_exists=True)

# 4) Agent ko knowledge do
agent = Agent(
    name="store_support",
    model=get_model(),
    knowledge=knowledge,
    search_knowledge=True,          # agentic RAG
    instructions=["Always search the knowledge base for store questions",
                  "If the info is not found, clearly say 'I don't know' — never guess"],
    markdown=True,
)

agent.print_response("Can I return a watch after 10 days?", stream=True)
agent.print_response("Is the Black Leather Chrono in stock? Price?", stream=True)
agent.print_response("What is the capital of Pakistan?", stream=True)   # knowledge mein nahi
