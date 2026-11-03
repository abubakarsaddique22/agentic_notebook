import hashlib  # Reproducible document IDs banata hai.
from pathlib import Path  # File paths OS independent banata hai.
from langchain_chroma import Chroma  # Persistent Chroma vectorstore integration.
from langchain_ollama import OllamaEmbeddings  # Ollama embeddings API.
from langchain_core.documents import Document  # Text ke saath metadata container.
from langchain_text_splitters import RecursiveCharacterTextSplitter  # Chunk splitting.
from settings import ROOT, settings
COLLECTION = 'level8_policy_kb'

def get_store():
    # model = embedding model ka naam; base_url = running Ollama ka address.
    embed = OllamaEmbeddings(model=settings.embedding_model, base_url=settings.ollama_base_url)
    return Chroma(collection_name=COLLECTION, embedding_function=embed, persist_directory=settings.chroma_dir)

def ingest_docs():
    paths = sorted((ROOT / 'data').glob('*.md'))
    if not paths: raise RuntimeError('data directory mein .md documents missing hain')
    import json  # Metadata labels trusted operator set karta hai.
    manifest = json.loads((ROOT / 'data/metadata.json').read_text(encoding='utf-8'))
    docs = [Document(page_content=p.read_text(encoding='utf-8'), metadata={
        'source': p.name, 'trust': 'external',
        'tenant_id': manifest.get(p.name, {}).get('tenant_id', 'public'),
        'classification': manifest.get(p.name, {}).get('classification', 'internal')
    }) for p in paths]
    chunks = RecursiveCharacterTextSplitter(chunk_size=650, chunk_overlap=80).split_documents(docs)
    store = get_store()
    # Reingest pe stale/duplicate records remove karte hain, deterministic IDs re-add hote hain.
    existing = store.get(include=[]).get('ids', [])
    if existing: store.delete(ids=existing)
    ids = [hashlib.sha256(f"{c.metadata['source']}:{i}:{c.page_content}".encode()).hexdigest() for i,c in enumerate(chunks)]
    store.add_documents(chunks, ids=ids)
    return len(chunks)

def tenant_filter(tenant_id: str = 'public') -> dict:
    # Chroma's database-side metadata filter; no unscoped retrieval.
    if tenant_id == 'public':
        return {'tenant_id': 'public'}
    return {'$or': [{'tenant_id': 'public'}, {'tenant_id': tenant_id}]}

def retrieve(query: str, tenant_id: str = 'public'):
    return get_store().similarity_search(query, k=settings.top_k, filter=tenant_filter(tenant_id))
