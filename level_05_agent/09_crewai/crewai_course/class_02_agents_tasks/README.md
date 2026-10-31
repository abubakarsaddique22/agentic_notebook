# Class 02 — Agents aur Tasks Deep Dive

| File | Concept |
|---|---|
| `01_agent_attributes.py` | Agent settings: `max_iter`, `max_rpm`, `max_execution_time`, `allow_delegation`, `inject_date` |
| `02_task_inputs.py` | **Dynamic inputs** `{placeholder}` + `output_file`, `markdown` |
| `03_task_context.py` | **Task context** — ek task ka output doosre ko dena |

## Yaad rakhne wali baatein
- `expected_output` jitna clear hoga, jawab utna behtar hoga. Format batao: "3 bullets", "JSON", "100 words".
- `{topic}` placeholder agent ke role/goal/backstory aur task description, sab mein chalta hai.
- `max_rpm` free APIs (Groq) ke liye bahut kaam ka hai — rate limit error se bachata hai.
- Sequential crew mein default: har task ko **pichle task** ka output milta hai. Zyada chahiye to `context=[...]`.

## Run
```
uv run python class_02_agents_tasks\01_agent_attributes.py
uv run python class_02_agents_tasks\02_task_inputs.py
uv run python class_02_agents_tasks\03_task_context.py
```

## Practice
- `02_task_inputs.py` mein teesra input `{length}` add karo (e.g. "200 words").
- `03_task_context.py` mein judge ko sirf `cons_task` ka context do — faisla kaise badla?
