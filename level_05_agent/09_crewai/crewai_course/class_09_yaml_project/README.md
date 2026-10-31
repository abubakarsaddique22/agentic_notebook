# Class 09 — YAML Project, Batch/Async, Callbacks, Planning

| File | Concept |
|---|---|
| `watch_review_crew/` | **Official project structure** — `config/agents.yaml`, `config/tasks.yaml`, `crew.py` (`@CrewBase`) |
| `01_run_yaml_crew.py` | YAML crew chalana + `@before_kickoff` / `@after_kickoff` |
| `02_batch_and_async.py` | `kickoff_for_each`, `akickoff` + `asyncio.gather`, `async_execution` tasks |
| `03_callbacks.py` | `step_callback`, `task_callback`, `Task(callback=...)` |
| `04_planning.py` | Crew `planning=True` + Agent `planning_config` (reasoning) |

## Official CLI (asal project ke liye)
```
crewai create crew my_project     # ye poora folder structure bana deti hai
cd my_project
crewai install                    # dependencies
crewai run                        # crew chalao
crewai create flow my_flow        # Flow project
```
Is class ka `watch_review_crew/` bilkul usi structure pe hai, bas chhota.

## YAML ka rule
`agents.yaml` mein agent ka naam **=** `crew.py` mein `@agent` function ka naam.
`tasks.yaml` mein task ka naam **=** `@task` function ka naam.

## Run
```
uv run python class_09_yaml_project\01_run_yaml_crew.py
uv run python class_09_yaml_project\02_batch_and_async.py
uv run python class_09_yaml_project\03_callbacks.py
uv run python class_09_yaml_project\04_planning.py
```
Groq free tier pe file 02 aur 04 mein "rate limit" error aaye to thora ruk ke dobara chalao, ya agents mein `max_rpm=5` lagao.
