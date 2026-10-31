# Class 06 — Memory aur Knowledge

| File | Concept |
|---|---|
| `01_memory_basics.py` | **Memory** standalone — `remember()` / `recall()` |
| `02_crew_with_memory.py` | **Crew memory** — 2 runs, doosri run pehli ko yaad rakhti hai |
| `03_knowledge_sources.py` | **Knowledge (RAG)** — String, Text file, CSV sources |
| `knowledge/` | Store policy + products CSV (fictional data) |

## Memory vs Knowledge
| | Memory | Knowledge |
|---|---|---|
| Kya hai | Kaam karte karte seekhi hui baatein | Pehle se diye gaye documents |
| Kaun likhta hai | CrewAI khud (har task ke baad) | Aap |
| Example | "Sara ko white dial pasand hai" | Return policy, product catalog |

## Embedder kya hai?
Text ko numbers (vector) mein badalna, taake "meaning" se search ho sake.
Hum `{"provider": "onnx"}` use kar rahe hain — **local aur free**. Pehli dafa ~80MB model download hoga.
Ollama ho to: `{"provider": "ollama", "config": {"model_name": "nomic-embed-text"}}`

## Run
```
uv run python class_06_memory_knowledge\01_memory_basics.py
uv run python class_06_memory_knowledge\02_crew_with_memory.py
uv run python class_06_memory_knowledge\03_knowledge_sources.py
```

## Memory saaf karni ho
```
crewai reset-memories --all
crewai reset-memories --knowledge
```
