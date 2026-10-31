"""
=====================================================================
 CLASS 07 | FILE 04: hybrid_and_traditional_rag.py
=====================================================================
 CONCEPT: Search types + Traditional vs Agentic RAG
 Search types (LanceDb search_type=...):
   SearchType.vector  -> meaning se dhoondo ("ghari wapas" ~ "return")
   SearchType.keyword -> exact lafz se (product codes, naam)
   SearchType.hybrid  -> DONO mila ke (production mein best)

 RAG ke 2 tareeqe:
   Agentic RAG     -> search_knowledge=True. Agent ko tool milta hai,
                      zaroorat ho to dhoondta hai. (flexible)
   Traditional RAG -> add_knowledge_to_context=True, search_knowledge=False
                      HAR sawal pe pehle search, results prompt mein.
                      (simple, predictable, lekin har dafa search)

 Run:
     uv run python class_07_knowledge_rag/04_hybrid_and_traditional_rag.py
=====================================================================
"""

from pathlib import Path

from agno.agent import Agent
from agno.knowledge.knowledge import Knowledge
from agno.vectordb.lancedb import LanceDb, SearchType

from llm_setup import get_model, get_embedder

KNOWLEDGE_DIR = Path(__file__).parent / "knowledge"

knowledge = Knowledge(
    name="hybrid_store",
    vector_db=LanceDb(
        uri="tmp/lancedb",
        table_name="hybrid_store",
        embedder=get_embedder(),
        search_type=SearchType.hybrid,      # vector + keyword
    ),
)
knowledge.insert(name="policy", path=str(KNOWLEDGE_DIR / "store_policy.txt"), skip_if_exists=True)
knowledge.insert(name="products", path=str(KNOWLEDGE_DIR / "products.csv"), skip_if_exists=True)

question = "What is the warranty and price of the Gold Dial Executive?"

# ---------- Agentic RAG ----------
agentic = Agent(model=get_model(), knowledge=knowledge, search_knowledge=True, markdown=True)
print("\n>>> AGENTIC RAG")
agentic.print_response(question)

# ---------- Traditional RAG ----------
traditional = Agent(
    model=get_model(),
    knowledge=knowledge,
    search_knowledge=False,
    add_knowledge_to_context=True,   # har sawal pe khud search + prompt mein
    markdown=True,
)
print("\n>>> TRADITIONAL RAG")
traditional.print_response(question)
