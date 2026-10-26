import os
import re
import glob

from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

load_dotenv()

DATA_DIR = "data"

# RAG ke embeddings kahan se aayein:
#   ollama      (default) -- local, free. Model: RAG_EMBED_MODEL (default nomic-embed-text)
#   openrouter            -- purana setup (text-embedding-3-large), credits chahiye
RAG_EMBED_PROVIDER = os.getenv("RAG_EMBED_PROVIDER", "ollama")
RAG_EMBED_MODEL = os.getenv("RAG_EMBED_MODEL", "nomic-embed-text")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

# har embedding model ka apna vector store (dimensions alag hote hain, mix nahi kar sakte)
if RAG_EMBED_PROVIDER == "openrouter":
    DB_DIR = "chroma_store_final"
else:
    DB_DIR = "chroma_store_" + RAG_EMBED_MODEL.replace(":", "_").replace("/", "_")


# 1. LOAD ---- read each transcript, throw away the VTT timestamps
def load_transcripts():

    docs = []
    for path in glob.glob(f"{DATA_DIR}/*.vtt"):
        lines = []
        for line in open(path):
            line = line.strip()
            if not line or line == "WEBVTT" or "-->" in line:
                continue
            lines.append(line)
        text = " ".join(lines)

        session = re.search(r"Session[ _]*(\d+)", path).group(1)

        docs.append(Document(page_content=text, metadata={"session": session}))

    return docs


# 2. BUILD ---- chunk, embed once, and keep it on disk so we don't re-embed
def load_store():
    if RAG_EMBED_PROVIDER == "openrouter":
        embeddings = OpenAIEmbeddings(
            model="openai/text-embedding-3-large",
            openai_api_key=os.environ.get("OPENROUTER_API_KEY"),
            openai_api_base="https://openrouter.ai/api/v1",
        )
    else:
        embeddings = OllamaEmbeddings(model=RAG_EMBED_MODEL, base_url=OLLAMA_HOST)

    if os.path.exists(DB_DIR):
        store = Chroma(persist_directory=DB_DIR, embedding_function=embeddings)
        # pichla build beech ma toota ho to folder khali reh jata ha -> dobara banao
        if store._collection.count() > 0:
            return store
        print(f"{DB_DIR} khali mila, dobara build kar rahe hain ...")
        store.delete_collection()

    docs = load_transcripts()

    chunks = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150,
    ).split_documents(docs)

    print(f"Built {len(chunks)} chunks from {len(docs)} transcripts, embedding with "
          f"{RAG_EMBED_PROVIDER}:{RAG_EMBED_MODEL} into {DB_DIR} ...")

    return Chroma.from_documents(chunks, embeddings, persist_directory=DB_DIR)


def build_retriever():
    return load_store().as_retriever(search_kwargs={"k": 5})


# 3. TRY IT ---- python src/retriever.py
if __name__ == "__main__":

    retriever = build_retriever()

    results = retriever.invoke("How will you evaluate a rag application?")
    
    for r in results:
        print(f"[Session {r.metadata['session']}] {r.page_content[:150]}...\n")
