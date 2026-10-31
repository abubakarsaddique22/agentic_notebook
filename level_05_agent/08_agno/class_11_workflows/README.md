# Class 11 — Workflows

| File | Concept |
|---|---|
| `01_sequential.py` | **Step(agent)** + **Step(executor=function)**, `step_results` |
| `02_parallel.py` | **Parallel** — kayi sources ek saath |
| `03_loop.py` | **Loop** — `end_condition` + `max_iterations` |
| `04_condition.py` | **Condition** — if / else (`else_steps`) |
| `05_router.py` | **Router** — kayi raston mein se ek |
| `06_state_team_steps.py` | Workflow **session_state**, **Team as step**, **Steps** group, **db** |
| `07_human_review.py` | **HumanReview** — workflow HITL (confirm + output review) |

## Team vs Workflow
| | Team | Workflow |
|---|---|---|
| Order kaun decide karta hai | Leader (LLM) | Aap (code) |
| Predictable | Kam | Bohot |
| Kab | Open-ended kaam | Fix business process |

**Best practice:** Workflow se control rakho, jahan "sochna" ho wahan step mein Agent ya Team daal do.

## Function step yaad karo
```python
def my_step(step_input: StepInput, run_context: RunContext) -> StepOutput:
    pichla = step_input.previous_step_content
    run_context.session_state["x"] = 1
    return StepOutput(content="...")
```

## Run
```
uv run python class_11_workflows\01_sequential.py
uv run python class_11_workflows\02_parallel.py
uv run python class_11_workflows\03_loop.py
uv run python class_11_workflows\04_condition.py
uv run python class_11_workflows\05_router.py
uv run python class_11_workflows\06_state_team_steps.py
uv run python class_11_workflows\07_human_review.py
```
