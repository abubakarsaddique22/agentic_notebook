# CrewAI Complete Course — 10 Classes (Roman Urdu)

CrewAI version: **1.15.x** (latest docs ke mutabiq). Har `.py` file ke shuru mein likha hai ke wo **kaunsa concept** sikhati hai.

## Classes
| # | Folder | Concepts |
|---|---|---|
| 01 | `class_01_basics` | Agent, Task, Crew, kickoff |
| 02 | `class_02_agents_tasks` | Agent settings, dynamic `{inputs}`, task context, output_file |
| 03 | `class_03_processes` | Sequential, Hierarchical, custom manager, delegation |
| 04 | `class_04_tools` | Built-in tools, `@tool`, `BaseTool`, caching |
| 05 | `class_05_llm_output_guardrails` | LLM config, structured output (Pydantic), **Guardrails** |
| 06 | `class_06_memory_knowledge` | **Memory**, **Knowledge (RAG)** |
| 07 | `class_07_flows_basics` | **Flows (Workflow)**: `@start`, `@listen`, state |
| 08 | `class_08_flows_advanced` | `@router`, `and_/or_`, **HITL**, `@persist`, Crew inside Flow |
| 09 | `class_09_yaml_project` | YAML project (`@CrewBase`), batch/async, callbacks, planning |
| 10 | `class_10_production` | **MCP**, event listeners, **hooks**, test/train, **Capstone project** |

## Concept → File (jaldi dhoondne ke liye)
| Concept | File |
|---|---|
| Agent / Task / Crew | `class_01_basics/02_first_crew.py` |
| Hierarchical process | `class_03_processes/02_hierarchical.py` |
| Custom tool | `class_04_tools/02_custom_tool_decorator.py` |
| Structured output | `class_05_llm_output_guardrails/02_structured_output.py` |
| **Guardrail (task)** | `class_05_llm_output_guardrails/03_guardrails.py` |
| **Guardrail (tool)** | `class_10_production/03_hooks_tool_guardrail.py` |
| Memory | `class_06_memory_knowledge/01_memory_basics.py` |
| Knowledge / RAG | `class_06_memory_knowledge/03_knowledge_sources.py` |
| **Workflow (Flow)** | `class_07_flows_basics/01_first_flow.py` |
| Router (if/else) | `class_08_flows_advanced/01_router.py` |
| **HITL (task)** | `class_08_flows_advanced/03_hitl_task_input.py` |
| **HITL (flow)** | `class_08_flows_advanced/04_hitl_flow_feedback.py` |
| **HITL (tool)** | `class_10_production/03_hooks_tool_guardrail.py` |
| Persistence | `class_08_flows_advanced/05_persist_resume.py` |
| YAML project | `class_09_yaml_project/watch_review_crew/` |
| MCP | `class_10_production/01_mcp_tools.py` |
| Observability | `class_10_production/02_event_listeners.py` |

## Setup (Windows — Command Prompt)
```
cd crewai_course
uv venv --python 3.12
.venv\Scripts\activate
uv sync
copy .env.example .env
notepad .env
```
**Default LLM: Ollama `gpt-oss:20b-cloud`.** Ye cloud model hai, PC pe bara download nahi hota:
1. [ollama.com/download](https://ollama.com/download) se Ollama install karo aur app chalu rakho.
2. Ek dafa sign in karo (free account):
```
ollama signin
ollama run gpt-oss:20b-cloud "hi"
```
Jawab aa gaya to setup theek hai.

**Groq use karna ho:** `.env` mein `LLM_PROVIDER=groq` aur `GROQ_API_KEY` daalo (free key: console.groq.com). Model: `openai/gpt-oss-120b`.

**Language:** Saare agent roles, goals, backstories, task descriptions, prompts aur tool descriptions **English** mein hain. Sirf files ke upar `CONCEPT` wali explanation aur README Roman Urdu mein hain.

## Har file kaise chalayein
Hamesha **course folder** (`crewai_course`) se chalao:
```
uv run python class_01_basics\01_first_agent.py
```

## `llm_setup.py` kya hai?
Har class folder mein ek hi jaisi `llm_setup.py` hai. Ye `.env` parh ke `get_llm()` deti hai, taake har file mein API key/model na likhna pare. Embeddings ke liye local `onnx` use hota hai (free, key nahi chahiye — pehli dafa ~80MB download).

## Common masle
| Error | Hal |
|---|---|
| `rate limit` / 429 | Groq free tier — 1 minute ruk ke chalao, ya agent mein `max_rpm=5` |
| `model ... decommissioned` | `.env` mein `GROQ_MODEL` naya daalo (Groq console → Models) |
| `Connection refused` / `localhost:11434` | Ollama app band hai — Start menu se Ollama chalao |
| `unauthorized` / `401` (Ollama) | `ollama signin` dobara chalao |
| `UnicodeEncodeError` (emoji) | cmd mein pehle `set PYTHONUTF8=1` chalao, ya Windows Terminal use karo |
| `Failed to connect to OpenAI API` (Groq use karte hue) | Normal label hai (Groq OpenAI-style API hai) — internet aur `GROQ_API_KEY` check karo |
| `ModuleNotFoundError: llm_setup` | Command course folder se chalao, class folder ke andar se nahi |
| Memory/knowledge purani baatein | `crewai reset-memories --all` |

`outputs\` folder mein files (blogs, reports) save hoti hain.
