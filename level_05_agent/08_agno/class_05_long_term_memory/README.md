# Class 05 — Long-Term Memory (User Memories)

| File | Concept |
|---|---|
| `01_user_memory_automatic.py` | **update_memory_on_run** — har run ke baad facts khud save, nayi chat mein bhi yaad |
| `02_agentic_memory.py` | **enable_agentic_memory** — agent khud add / update / delete karta hai |
| `03_memory_manager.py` | **MemoryManager** — kya save ho (instructions), alag model, clear |

## Short-term vs Long-term
| | Short-term (Class 03) | Long-term (Class 05) |
|---|---|---|
| Kis ki | Ek **session** (conversation) | Ek **user** |
| Key | `session_id` | `user_id` |
| Kya | Messages / summary | Facts ("Ali ko cricket pasand hai") |
| Example | ChatGPT ki ek chat | ChatGPT ki "Memory" setting |

## Automatic vs Agentic
| | `update_memory_on_run=True` | `enable_agentic_memory=True` |
|---|---|---|
| Kab chalti hai | Har run ke baad | Jab agent zaroori samjhe |
| Cost | Har dafa extra LLM call | Kam |
| Control | Kam | Agent update/delete bhi kar sakta hai |

## Run
```
uv run python class_05_long_term_memory\01_user_memory_automatic.py
uv run python class_05_long_term_memory\02_agentic_memory.py
uv run python class_05_long_term_memory\03_memory_manager.py
```
