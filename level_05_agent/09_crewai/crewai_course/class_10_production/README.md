# Class 10 — Production Features + Capstone Project

| File | Concept |
|---|---|
| `01_mcp_tools.py` + `watch_mcp_server.py` | **MCP** — `Agent(mcps=[MCPServerStdio(...)])` |
| `02_event_listeners.py` | **Event listeners / Observability** — `BaseEventListener` |
| `03_hooks_tool_guardrail.py` | **Execution hooks** — `@before_tool_call` (tool guardrail + HITL approval), `@after_tool_call` |
| `04_test_and_train.py` | **crew.test()** (score) + **crew.train()** (human feedback se seekhna) |
| `05_capstone_support_flow.py` | **FINAL PROJECT** — poore course ke concepts ek system mein |
| `knowledge/` | Capstone ke liye store policy + products |

## Guardrails — 3 levels (yaad kar lo)
| Level | Kya check karta hai | Kaise |
|---|---|---|
| Task guardrail | Task ka **output** | `Task(guardrail=fn)` / `guardrails=[...]` (class 05) |
| Tool hook | Tool chalne se **pehle** | `@before_tool_call` → `return False` = block |
| HITL | Insaan ki approval | `human_input=True`, `@human_feedback`, `context.request_human_input()` |

## Capstone flow
```
classify ─▶ route ─┬─ order_status ─▶ check_order ──┐
                   ├─ product ──────▶ product_crew ─┼─▶ review (HUMAN) ─send─▶ send_reply
                   └─ complaint ────▶ complaint ────┘        │
                                                 ▲──rewrite──┘
```
Run karo aur ye 3 messages try karo:
1. `Where is order 1002?`
2. `How long is the warranty on the Gold Dial Executive?`
3. `The glass of my watch broke, terrible quality!`

Review pe ek dafa "make it shorter" likho — reply dobara banega.

## Run
```
uv run python class_10_production\01_mcp_tools.py
uv run python class_10_production\02_event_listeners.py
uv run python class_10_production\03_hooks_tool_guardrail.py
uv run python class_10_production\04_test_and_train.py
uv run python class_10_production\05_capstone_support_flow.py
```

## Aage kya?
- Capstone ko FastAPI endpoint ke peeche lagao (WhatsApp webhook → `SupportFlow().kickoff(...)`).
- `lookup_order` ko asli database/Shopify API se jodo.
- Official CLI se project banao: `crewai create flow support_system`.
