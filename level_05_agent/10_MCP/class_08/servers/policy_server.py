"""Policy MCP: cached document embeddings, semantic search with Gemini."""
import asyncio
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from mcp.server import MCPServer

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from rag_utils import cosine, file_hash

load_dotenv(ROOT.parent / ".env")
DOC = ROOT / "data" / "company_policy.md"
INDEX = ROOT / "data" / "policy_index.json"
server = MCPServer("Company Policy RAG MCP Server")


def search_sync(query: str, top_k: int) -> dict:
    if not query.strip():
        return {"success": False, "error": "query cannot be empty"}
    if not INDEX.exists():
        return {"success": False, "error": "Index missing. Run: python build_index.py"}
    if not os.getenv("GOOGLE_API_KEY"):
        return {"success": False, "error": "GOOGLE_API_KEY is missing"}

    data = json.loads(INDEX.read_text(encoding="utf-8"))
    if data.get("source_sha256") != file_hash(DOC):
        return {"success": False, "error": "Policy changed. Re-run: python build_index.py"}
    if data.get("model") != "gemini-embedding-2":
        return {"success": False, "error": "Model mismatch. Rebuild index"}

    # Identical embedding model used for indexing and retrieval
    model = GoogleGenerativeAIEmbeddings(model=data["model"])
    query_vector = model.embed_query(query)
    ranked = sorted(
        (
            {
                "chunk_id": chunk["chunk_id"],
                "source": chunk["source"],
                "text": chunk["text"],
                "score": round(cosine(query_vector, chunk["embedding"]), 4),
            }
            for chunk in data["chunks"]
        ),
        key=lambda x: x["score"], reverse=True
    )
    k = max(1, min(int(top_k), 5))
    return {"success": True, "query": query, "matches": ranked[:k],
            "note": "Cosine scores rank passages; they are not confidence probabilities.",
            "demo_policy": True}


@server.tool()
async def search_company_policy(query: str, top_k: int = 3) -> dict:
    """Semantic retrieval of demo company travel rules using Gemini embeddings."""
    try:
        return await asyncio.to_thread(search_sync, query, top_k)
    except Exception as exc:
        return {"success": False, "error": f"Search failed: {type(exc).__name__}: {exc}"}


@server.resource("policy://travel-summary")
def policy_summary() -> str:
    """Example policy source; for direct reading (no vector search)."""
    return DOC.read_text(encoding="utf-8")


if __name__ == "__main__":
    server.run(transport="streamable-http", host="127.0.0.1", port=8002,
               stateless_http=True, json_response=True)
