
import asyncio
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from mcp.server import MCPServer

# 1. Project paths
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from rag_utils import cosine, file_hash

load_dotenv()

DOC = ROOT / "data" / "company_policy.md"
INDEX = ROOT / "data" / "policy_index.json"

# 2. Create MCP Server
server = MCPServer("Company Policy RAG MCP Server")


# =========================
# 3. SEMANTIC SEARCH
# =========================

def search_policy(query: str, top_k: int = 3) -> dict:

    # Check query
    if not query.strip():
        return {"success": False, "error": "Query is empty"}

    # Check index
    if not INDEX.exists():
        return {"success": False, "error": "Run python build_index.py first"}

    # Check API key
    if not os.getenv("GOOGLE_API_KEY"):
        return {"success": False, "error": "Missing GOOGLE_API_KEY"}

    # Load saved embeddings
    data = json.loads(INDEX.read_text(encoding="utf-8"))

    # Check policy document
    if not DOC.exists():
        return {"success": False, "error": "Policy document missing"}

    if data["source_sha256"] != file_hash(DOC):
        return {"success": False, "error": "Policy changed. Rebuild index"}

    # Gemini Embedding Model
    if data["model"] != "gemini-embedding-2":
        return {"success": False, "error": "Embedding model mismatch"}

    embeddings = GoogleGenerativeAIEmbeddings(
        model="gemini-embedding-2"
    )

    # Convert user query into vector
    query_vector = embeddings.embed_query(query)

    # Compare query with document chunks
    results = []

    for chunk in data["chunks"]:

        score = cosine(
            query_vector,
            chunk["embedding"]
        )

        results.append({
            "chunk_id": chunk["chunk_id"],
            "source": chunk["source"],
            "text": chunk["text"],
            "score": round(score, 4)
        })

    # Sort highest similarity first
    results.sort(
        key=lambda item: item["score"],
        reverse=True
    )

    # Return top matches
    top_k = max(1, min(top_k, 5))

    return {
        "success": True,
        "query": query,
        "matches": results[:top_k],
        "demo_policy": True
    }


# =========================
# 4. MCP TOOL
# =========================

@server.tool()
async def search_company_policy(query: str, top_k: int = 3) -> dict:
    """Search company policies using Gemini embeddings."""

    try:
        return await asyncio.to_thread(
            search_policy, query, top_k
        )

    except Exception as error:
        return {
            "success": False,
            "error": str(error)
        }


# =========================
# 5. MCP RESOURCE
# =========================

@server.resource("policy://travel-summary")
def policy_summary() -> str:
    """Read complete company policy document."""

    return DOC.read_text(encoding="utf-8")


# =========================
# 6. RUN MCP SERVER
# =========================

if __name__ == "__main__":
    server.run(
        transport="streamable-http",
        host="127.0.0.1",
        port=8002,
        stateless_http=True,
        json_response=True
    )
