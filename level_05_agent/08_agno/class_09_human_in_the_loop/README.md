# Class 09 — Human-in-the-Loop (HITL)

| File | Concept |
|---|---|
| `01_confirmation.py` | **requires_confirmation** — tool se pehle y/n approval |
| `02_user_input.py` | **requires_user_input** — kuch fields insaan bhare |
| `03_external_execution.py` | **external_execution** — tool aap khud (bahar) chalao |

Workflow wala HITL (`HumanReview`) class 11 mein hai.

## HITL ka pattern (teeno files mein same)
```python
run_output = agent.run("...")
if run_output.is_paused:
    for req in run_output.active_requirements:
        if req.needs_confirmation:        req.confirm() / req.reject()
        if req.needs_user_input:          req.provide_user_input({...})
        if req.needs_external_execution:  req.set_external_execution_result("...")
    run_output = agent.continue_run(run_response=run_output)
```

## Real app mein
Terminal ke `input()` ki jagah WhatsApp / web button pe approval aata hai. `db` lagao to paused run save rehta hai aur ghanton baad bhi `continue_run(run_id=...)` se chal sakta hai.

## Run
```
uv run python class_09_human_in_the_loop\01_confirmation.py
uv run python class_09_human_in_the_loop\02_user_input.py
uv run python class_09_human_in_the_loop\03_external_execution.py
```
