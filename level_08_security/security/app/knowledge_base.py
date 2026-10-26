"""Knowledge base: loads store docs into a Chroma vector store.

Each doc starts with a header like `<!-- audience: public -->`. We store that
as metadata, but v0 of the app does NOT use it when searching. That is
vulnerability V5 in the threat model (internal docs reachable by customers),
and we fix it in M8.5.

Build the index:  python -m app.knowledge_base
"""
import re
import shutil
import uuid
from functools import lru_cache

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import CHROMA_DIR, DOCS_DIR, get_embeddings

COLLECTION = "store_kb"
_AUDIENCE_RE = re.compile(r"<!--\s*audience:\s*(\w+)\s*-->")


def load_docs() -> list[Document]:
    docs = []
    for path in sorted(DOCS_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        match = _AUDIENCE_RE.search(text)
        audience = match.group(1) if match else "public"
        text = _AUDIENCE_RE.sub("", text).strip()
        docs.append(Document(page_content=text, metadata={"source": path.name, "audience": audience}))
    return docs


def build_index(reset: bool = True) -> int:
    if reset and CHROMA_DIR.exists():
        shutil.rmtree(CHROMA_DIR)
    get_store.cache_clear()
    splitter = RecursiveCharacterTextSplitter(chunk_size=600, chunk_overlap=80)
    chunks = splitter.split_documents(load_docs())
    Chroma.from_documents(
        chunks,
        embedding=get_embeddings(),
        collection_name=COLLECTION,
        persist_directory=str(CHROMA_DIR),
    )
    return len(chunks)


@lru_cache(maxsize=1)
def get_store() -> Chroma:
    return Chroma(
        collection_name=COLLECTION,
        embedding_function=get_embeddings(),
        persist_directory=str(CHROMA_DIR),
    )


def search(query: str, k: int = 3) -> list[Document]:
    # VULN V5: no filter on metadata["audience"], so internal notes can be retrieved.
    return get_store().similarity_search(query, k=k)


def add_docs(docs: list[Document]) -> list[str]:
    """Add documents to the live index (used to simulate poisoned content). Returns their ids."""
    ids = [f"tmp-{uuid.uuid4().hex}" for _ in docs]
    get_store().add_documents(docs, ids=ids)
    return ids


def delete_ids(ids: list[str]) -> None:
    if ids:
        get_store().delete(ids=ids)


if __name__ == "__main__":
    n = build_index(reset=True)
    print(f"Indexed {n} chunks from {DOCS_DIR}")
    for doc in search("staff discount coupon", k=2):
        print(f"- {doc.metadata['source']} ({doc.metadata['audience']})")
