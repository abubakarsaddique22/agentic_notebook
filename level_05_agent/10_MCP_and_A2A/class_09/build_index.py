"""Run once and whenever policy docs change. Uses real Gemini API."""
import json
import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from rag_utils import chunk_markdown, file_hash

ROOT = Path(__file__).resolve().parent
DOC = ROOT / "data" / "company_policy.md"
INDEX = Path(os.getenv("POLICY_INDEX_PATH", str(ROOT / "data" / "index_storage" / "policy_index.json")))
MODEL = "gemini-embedding-2"


def main():
    load_dotenv(ROOT.parent / ".env")
    if not os.getenv("GOOGLE_API_KEY"):
        raise RuntimeError("Set GOOGLE_API_KEY in MCP_Practical/.env")
    chunks = chunk_markdown(DOC.read_text(encoding="utf-8"))
    if not chunks:
        raise RuntimeError("Source policy document is empty")

    embeddings = GoogleGenerativeAIEmbeddings(model=MODEL)
    vectors = embeddings.embed_documents([c["text"] for c in chunks])
    if len(vectors) != len(chunks):
        raise RuntimeError("Embedding count does not match chunks")
    for c, v in zip(chunks, vectors):
        c["embedding"] = v
        c["source"] = DOC.name
    payload = {
        "model": MODEL,
        "source_sha256": file_hash(DOC),
        "chunks": chunks,
    }
    INDEX.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Indexed {len(chunks)} chunks, dimension={len(vectors[0])}, at {INDEX}")


if __name__ == "__main__":
    main()
