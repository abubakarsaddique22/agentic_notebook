# Class 07 — Knowledge aur RAG

| File | Concept |
|---|---|
| `01_knowledge_basics.py` | **Knowledge + LanceDB + Embedder**, `insert()` (text, txt, csv), **agentic RAG** |
| `02_pdf_rag.py` | **PDFReader + Chunking** (Recursive / Semantic), seedha `knowledge.search()` |
| `03_metadata_filters.py` | **metadata + knowledge_filters**, agentic filters |
| `04_hybrid_and_traditional_rag.py` | **Hybrid search**, Agentic vs **Traditional RAG** |
| `knowledge/` | Store policy, products CSV, *Attention Is All You Need* PDF |

## RAG pipeline
```
Document ─▶ Reader ─▶ Chunking ─▶ Embedder ─▶ Vector DB (LanceDB)
                                                    │
User sawal ─▶ Embedder ─▶ similar chunks dhoondo ◀──┘ ─▶ Model ─▶ Jawab
```

## Embedder
`llm_setup.get_embedder()` → default **FastEmbed** (local, free, 384 dims). Ollama chahiye to `.env` mein `EMBEDDER_PROVIDER=ollama` (pehle `ollama pull nomic-embed-text`).

> **Dimensions ka dhyan:** embedder aur vector table ke dimensions same hone chahiye. Embedder badlo to `tmp\lancedb` folder delete karke dobara chalao.

## Agno 3.x note
Purane tutorials mein `knowledge.add_content(...)` hai — Agno 3.x mein ye **`knowledge.insert(...)`** hai.

## Run
```
uv run python class_07_knowledge_rag\01_knowledge_basics.py
uv run python class_07_knowledge_rag\02_pdf_rag.py
uv run python class_07_knowledge_rag\03_metadata_filters.py
uv run python class_07_knowledge_rag\04_hybrid_and_traditional_rag.py
```
