# Class 03 — Processes (Sequential vs Hierarchical)

| File | Concept |
|---|---|
| `01_sequential.py` | **Sequential** — tasks line mein, ek ke baad ek |
| `02_hierarchical.py` | **Hierarchical** — CrewAI ka auto manager kaam baantta hai (`manager_llm`) |
| `03_custom_manager.py` | **Custom manager** (`manager_agent`) + **delegation** |

## Comparison
| | Sequential | Hierarchical |
|---|---|---|
| Kaam kaun baantta hai | Aap (har task pe `agent=`) | Manager agent |
| Order | Fix | Manager decide karta hai |
| Cost | Kam tokens | Zyada (manager ki extra calls) |
| Kab use | Fix pipeline | Kaam open-ended ho, routing chahiye |

## Rules
- Hierarchical mein `manager_llm` **ya** `manager_agent` lazmi hai.
- Custom manager ko `agents=[]` list mein mat daalo.
- `allow_delegation=True` = agent doosron ko kaam de sakta hai.

## Run
```
uv run python class_03_processes\01_sequential.py
uv run python class_03_processes\02_hierarchical.py
uv run python class_03_processes\03_custom_manager.py
```
Tip: hierarchical mein `verbose=True` ka output dhyan se parho — "Delegate work to coworker" wale steps manager ke faislay hain.
