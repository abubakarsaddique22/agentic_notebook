# 02 — Tracing Basics (sabse important folder)

Industry mein 80% LangSmith usage **tracing** hai. Yeh folder achhi tarah samjho.

## Concepts

### 1. `@traceable` decorator
Kisi bhi function par lagao → wo ek **run** ban jata hai. Andar wale traceable functions **child runs** bante hain.

### 2. `run_type` — run kis qism ka hai
| run_type | Kab use karo | UI mein faida |
|---|---|---|
| `chain` (default) | General logic / pipeline step | — |
| `llm` | Khud ka LLM call (agar wrapper use nahi kar rahe) | Tokens, cost, chat view |
| `tool` | Agent ke tools (search, calculator, DB query) | Tool icon |
| `retriever` | RAG mein documents nikalna | Documents nicely render hote hain |
| `prompt` | Prompt formatting step | — |
| `embedding` | Embeddings banana | — |

### 3. `name`, `tags`, `metadata`
- **name**: UI mein run ka naam
- **tags**: list of strings — filter ke liye (`["v2", "rag"]`)
- **metadata**: dict — filter + context (`{"user_id": "u1", "prompt_version": "v3"}`)

Static (decorator mein) ya dynamic (`langsmith_extra=` se call ke waqt) — dono tareeqe.

### 4. `wrap_openai`
OpenAI SDK client (yahan Groq ke URL ke saath) ko wrap karo → har call automatically `llm` run, tokens/streaming sab track.

### 5. `trace()` context manager + `tracing_context()`
Jab decorator nahi laga sakte (e.g. code ka ek hissa trace karna hai) ya tracing temporarily band/redirect karni ho.

## Files (order mein chalao)
| File | Concept |
|---|---|
| `01_traceable_decorator.py` | nesting, run_type, name, tags, metadata, langsmith_extra |
| `02_wrap_openai.py` | wrapped client, streaming, JSON output |
| `03_trace_context_manager.py` | `ls.trace`, `tracing_context`, runtime metadata, tracing OFF |
| `04_run_types.py` | retriever/tool/llm run types sahi format ke saath |
| `05_errors_and_async.py` | errors trace mein kaise dikhte hain, async + parallel calls |

## UI Exercise
- Tracing project mein **Filter** → `tags` = `v2` lagao
- Metadata filter → `user_id` = `user_123`
- Error wale run (laal) par click karke stack trace dekho
