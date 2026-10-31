# Class 01 — Setup + Pehla Agent aur Crew

## Is class mein kya seekhenge
| File | Concept |
|---|---|
| `01_first_agent.py` | **Agent** — role, goal, backstory; `agent.kickoff()` se akela agent chalana |
| `02_first_crew.py` | **Agent + Task + Crew** — team bana ke `crew.kickoff()` |

## Concepts (asaan zubaan mein)
- **Agent** = ek AI employee. `role` (kaun hai), `goal` (kya chahta hai), `backstory` (iska experience).
- **Task** = ek kaam. `description` (kya karna hai) + `expected_output` (jawab kaisa dikhna chahiye).
- **Crew** = team. Agents + tasks ko jorti hai.
- **kickoff()** = start button.
- **verbose=True** = terminal mein agent ki "soch" (thoughts, steps) dikhti hai — debugging ke liye best.

## Result object
```python
result.raw            # aakhri task ka text
result.tasks_output   # har task ka alag output
result.token_usage    # kitne tokens lage
```

## Run (Windows cmd, course folder se)
```
uv run python class_01_basics\01_first_agent.py
uv run python class_01_basics\02_first_crew.py
```

## Practice
1. Teacher agent ka `role` badal ke "Strict Math Teacher" karo — jawab ka tone kaise badla?
2. Crew mein teesra agent "Editor" aur teesra task "post ko improve karo" add karo.
