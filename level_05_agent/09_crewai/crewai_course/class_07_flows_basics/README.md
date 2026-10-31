# Class 07 — Flows Part 1 (Workflow basics)

| File | Concept |
|---|---|
| `01_first_flow.py` | **Flow** — `@start`, `@listen`, steps ka data pass hona, `flow.plot()` |
| `02_flow_state.py` | **State** — unstructured (dict) vs structured (Pydantic) |
| `03_flow_with_ai.py` | Flow steps mein **LLM call + Agent** |

## Crew vs Flow
| | Crew | Flow |
|---|---|---|
| Control | Agents khud decide karte hain | Aap order fix karte ho |
| Predictable | Kam | Zyada |
| Kab use | Open-ended research/creative kaam | Production apps, fix business process |

**Best practice:** Flow se shuru karo. Jahan "sochne" wala kaam ho, wahan us step ke andar Agent ya Crew chalao.

## Decorators yaad karo
```python
@start()            # pehla step
@listen(step_name)  # step_name ke baad chalo
```

## Structured state
```python
class MyState(BaseModel):
    name: str = ""

class MyFlow(Flow[MyState]):
    ...  self.state.name ...
```

## Run
```
uv run python class_07_flows_basics\01_first_flow.py
uv run python class_07_flows_basics\02_flow_state.py
uv run python class_07_flows_basics\03_flow_with_ai.py
```
File 01 chalane pe flow ka diagram browser mein khud khul jayega (`flow.plot()`).
