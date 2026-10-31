# Agno Complete Course — 12 Classes

Agno version: **3.1.x** (latest). Har `.py` file ke shuru mein likha hai ke wo **kaunsa concept** sikhati hai.

**Language:** Saari agent instructions, descriptions, prompts, tool docstrings aur knowledge files **English** mein hain. Sirf samjhane wale comments / README Roman Urdu mein hain.

## Classes
| # | Folder | Concepts |
|---|---|---|
| 01 | `class_01_agents_models` | Agent, models (Groq/OpenRouter/Ollama/Gemini), instructions, `run()`, fallback models |
| 02 | `class_02_tools` | Built-in toolkits, custom function tools, `@tool` options, Toolkit class |
| 03 | `class_03_short_term_memory` | Sessions, chat history, multiple sessions, **session summaries** |
| 04 | `class_04_session_state` | **Session state**, tools with state (CRUD), **dependencies** |
| 05 | `class_05_long_term_memory` | **User memories**: automatic, agentic, MemoryManager |
| 06 | `class_06_structured_output_reasoning` | **output_schema**, **input_schema**, **Reasoning** |
| 07 | `class_07_knowledge_rag` | **Knowledge / RAG**: LanceDB, PDF + chunking, metadata filters, hybrid search |
| 08 | `class_08_guardrails_hooks` | **Guardrails** (built-in + custom), pre/post hooks, **tool hooks** |
| 09 | `class_09_human_in_the_loop` | **HITL**: confirmation, user input, external execution |
| 10 | `class_10_teams` | **Teams**: coordinate, route, broadcast, tasks, shared state |
| 11 | `class_11_workflows` | **Workflows**: sequential, parallel, loop, condition, router, state, **HumanReview** |
| 12 | `class_12_production` | **MCP**, async, **AgentOS**, **Evals**, **Capstone project** |

## Concept → File
| Concept | File |
|---|---|
| Agent + model | `class_01_agents_models/01_first_agent.py` |
| Custom tool | `class_02_tools/02_custom_function_tools.py` |
| Short-term memory | `class_03_short_term_memory/01_session_history.py` |
| Session summary | `class_03_short_term_memory/03_session_summary.py` |
| Session state + tools | `class_04_session_state/02_state_with_tools.py` |
| **Long-term memory** | `class_05_long_term_memory/01_user_memory_automatic.py` |
| Structured output | `class_06_structured_output_reasoning/01_output_schema.py` |
| Reasoning | `class_06_structured_output_reasoning/03_reasoning.py` |
| RAG (PDF) | `class_07_knowledge_rag/02_pdf_rag.py` |
| **Guardrail (input)** | `class_08_guardrails_hooks/01_builtin_guardrails.py` |
| **Guardrail (output)** | `class_08_guardrails_hooks/02_custom_guardrail.py` |
| **Guardrail (tool)** | `class_08_guardrails_hooks/04_tool_hooks.py` |
| **HITL (agent)** | `class_09_human_in_the_loop/01_confirmation.py` |
| **HITL (workflow)** | `class_11_workflows/07_human_review.py` |
| Team modes | `class_10_teams/` |
| **Workflow** | `class_11_workflows/01_sequential.py` |
| MCP | `class_12_production/01_mcp_tools.py` |
| AgentOS (API server) | `class_12_production/03_agent_os.py` |
| Evals | `class_12_production/04_evals.py` |

## Setup (Windows — Command Prompt)
```
cd agno_course
uv venv --python 3.12
.venv\Scripts\activate
uv sync
copy .env.example .env
notepad .env
```
`.env` mein `GROQ_API_KEY` daalo. OpenRouter / Ollama / Gemini ke liye `LLM_PROVIDER` badlo.

## Har file kaise chalayein
Hamesha **course folder** (`agno_course`) se:
```
uv run python class_01_agents_models\01_first_agent.py
```

## `llm_setup.py`
Har class folder mein same copy. `get_model()` `.env` se model deta hai, `get_embedder()` RAG ke liye local **FastEmbed** (free, key nahi chahiye, pehli dafa ~70MB download).

## Purane tutorials se farq (Agno 3.x)
| Purana | Naya (3.x) |
|---|---|
| `knowledge.add_content(...)` | `knowledge.insert(...)` |
| Tool mein `session_state: dict` | `run_context: RunContext` → `run_context.session_state` |
| `from mcp.server.fastmcp import FastMCP` | mcp 2.x: `from mcp.server.mcpserver import MCPServer` |
| `OpenRouter(id="gpt-4o-mini")` | `OpenRouter(id="openai/gpt-4o-mini")` |

## Common masle
| Error | Hal |
|---|---|
| `rate limit` / 429 | Groq free tier — 1 minute ruk jao, ya teams/tasks wali files kam chalao |
| `model ... decommissioned` | `.env` mein `GROQ_MODEL` naya daalo (Groq console → Models) |
| `query dim(...) doesn't match` | Embedder badla hai — `tmp\lancedb` folder delete karo |
| `UnicodeEncodeError` | cmd mein `set PYTHONUTF8=1` ya Windows Terminal use karo |
| `ModuleNotFoundError: llm_setup` | Command course folder se chalao |
| DuckDuckGo error | Internet / rate limit — thori der baad chalao |

Databases aur vector DB `tmp\` folder mein bante hain. Sab saaf karna ho to `tmp` delete kar do.
