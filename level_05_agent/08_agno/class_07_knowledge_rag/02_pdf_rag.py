"""
=====================================================================
 CLASS 07 | FILE 02: pdf_rag.py
=====================================================================
 CONCEPT: PDF RAG — Reader + Chunking strategy
 Kya hai :
   Reader   -> file parhne wala (PDFReader, CSVReader, WebsiteReader,
               DocxReader ...)
   Chunking -> text ko kaise kaatna hai:
     FixedSizeChunking   -> har 1000 characters (sab se simple)
     RecursiveChunking   -> paragraph/line pe kaatna (recommended start)
     SemanticChunking    -> MEANING badalne pe kaatna (embedder chahiye,
                            behtar lekin slow)
     DocumentChunking    -> poora page/section ek chunk
   chunk_size  -> ek tukre ki lambai
   overlap     -> do tukron mein thora common text (context na toote)

 PDF: knowledge/attention_is_all_you_need.pdf (Transformer paper)
 Pehli dafa chalane mein time lagega (embeddings ban rahi hain).

 Run:
     uv run python class_07_knowledge_rag/02_pdf_rag.py
=====================================================================
"""

from pathlib import Path

from agno.agent import Agent
from agno.knowledge.chunking.recursive import RecursiveChunking
from agno.knowledge.knowledge import Knowledge
from agno.knowledge.reader.pdf_reader import PDFReader
from agno.vectordb.lancedb import LanceDb

from llm_setup import get_model, get_embedder

PDF_PATH = Path(__file__).parent / "knowledge" / "attention_is_all_you_need.pdf"

reader = PDFReader(
    chunking_strategy=RecursiveChunking(chunk_size=1000, overlap=100),
)
# Semantic chunking try karna ho:
#   from agno.knowledge.chunking.semantic import SemanticChunking
#   reader = PDFReader(chunking_strategy=SemanticChunking(embedder=get_embedder(), chunk_size=1000))

knowledge = Knowledge(
    name="paper_knowledge",
    description="Research paper: 'Attention Is All You Need'",
    vector_db=LanceDb(uri="tmp/lancedb", table_name="attention_paper", embedder=get_embedder()),
)

knowledge.insert(name="attention_paper", path=str(PDF_PATH), reader=reader, skip_if_exists=True)

agent = Agent(
    name="paper_assistant",
    model=get_model(),
    knowledge=knowledge,
    search_knowledge=True,
    instructions=["Use the knowledge base for questions about the Transformer / paper",
                  "Mention which part of the paper the info comes from",
                  "If you don't know, say 'I don't know'"],
    markdown=True,
)

agent.print_response("What hardware was used to train the Transformer?", stream=True)
agent.print_response("How many layers were in the encoder and decoder stacks?", stream=True)

# ---------- Bina agent ke seedha search ----------
print("\n===== DIRECT SEARCH (top 2 chunks) =====")
for doc in knowledge.search(query="multi-head attention", max_results=2):
    print("-", doc.content[:150].replace("\n", " "), "...")
