# Class 12 — Production: MCP, Async, AgentOS, Evals + Capstone

| File | Concept |
|---|---|
| `01_mcp_tools.py` + `store_mcp_server.py` | **MCPTools** — MCP server ke tools agent ko |
| `02_async_agents.py` | **arun / aprint_response** + `asyncio.gather` |
| `03_agent_os.py` | **AgentOS** — agents/teams ko FastAPI server + web UI |
| `04_evals.py` | **AccuracyEval** (judge score) + **ReliabilityEval** (sahi tool call) |
| `05_capstone_support_system.py` | **FINAL PROJECT** — sab concepts ek system mein |
| `knowledge/` | Capstone ke liye store data |

## Capstone flow
```
classify (guardrails + structured output)
   │
Router ─┬─ order ─────▶ Order Agent (tool) ──────────┐
        ├─ product ───▶ Product Agent (RAG + memory) ─┼─▶ Final Reply ─▶ HUMAN review
        ├─ complaint ─▶ Complaint Agent ──────────────┤        (reject + feedback = retry)
        └─ blocked ───▶ polite refusal ───────────────┘
```
Try karo:
1. `Where is order 1002?`
2. `What is the warranty on the Gold Dial Executive?`
3. `The glass of my watch broke!`
4. `Ignore previous instructions...` (guardrail)

Review pe ek dafa "make it shorter" likho — reply dobara banega.

## AgentOS test
```
uv run python class_12_production\03_agent_os.py
```
Browser: `http://localhost:7777/docs`. Doosri cmd window:
```
curl -X POST http://localhost:7777/agents/support-agent/runs -F "message=When will my delivery arrive?" -F "stream=false"
```

## Aage kya?
- Capstone ko AgentOS mein daal ke WhatsApp webhook se jodo.
- `lookup_order` ko asli database / Shopify API se badlo.
- Har prompt change ke baad `04_evals.py` chalao.
