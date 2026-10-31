# Class 08 — Flows Part 2 (Router, HITL, Persist, Crew in Flow)

| File | Concept |
|---|---|
| `01_router.py` | **@router** — if/else branching (complaint / order / general) |
| `02_and_or.py` | **and_ / or_** — dono ka intezar / jo pehle aaye |
| `03_hitl_task_input.py` | **HITL (Crew)** — `Task(human_input=True)` |
| `04_hitl_flow_feedback.py` | **HITL (Flow)** — `@human_feedback` + approve / reject / revise loop |
| `05_persist_resume.py` | **@persist** — state save + same id se resume |
| `06_crew_inside_flow.py` | **Crew inside Flow** — production pattern |

## HITL (Human-in-the-Loop) — 3 jagah
| Kahan | Kaise | Kab use |
|---|---|---|
| Task | `human_input=True` | Crew ke output ko review karna |
| Flow step | `@human_feedback(...)` | Approval workflow, branching on human decision |
| Tool call | `@before_tool_call` hook (class 10) | Khatarnak tool (delete, payment) se pehle permission |

## @human_feedback yaad karo
```python
@human_feedback(
    message="Approve?",
    emit=["approved", "rejected", "needs_revision"],
    llm=llm,                     # emit ho to lazmi
    default_outcome="approved",  # Enter dabane pe
)
@listen(or_(start_step, "needs_revision"))
def draft(self): ...

@listen("approved")
def publish(self, result: HumanFeedbackResult): ...
```
`result.output` = jo dikhaya | `result.feedback` = jo aap ne likha | `result.outcome` = label

## Run
```
uv run python class_08_flows_advanced\01_router.py
uv run python class_08_flows_advanced\02_and_or.py
uv run python class_08_flows_advanced\03_hitl_task_input.py
uv run python class_08_flows_advanced\04_hitl_flow_feedback.py
uv run python class_08_flows_advanced\05_persist_resume.py
uv run python class_08_flows_advanced\06_crew_inside_flow.py
```
File 04 mein pehli dafa kuch changes likho (e.g. "price bhi add karo") — draft dobara banega. Phir Enter dabao = approved.
