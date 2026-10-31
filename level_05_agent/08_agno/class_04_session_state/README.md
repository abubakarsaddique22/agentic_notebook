# Class 04 — Session State aur Dependencies

| File | Concept |
|---|---|
| `01_session_state.py` | **session_state**, `{placeholders}` instructions mein, state update, `get_session_state` |
| `02_state_with_tools.py` | Tools jo **`run_context.session_state`** badalte hain (cart CRUD), alag session = alag cart |
| `03_dependencies_context.py` | **dependencies** — har run pe fresh data (functions) |

## Chat history vs Session state vs Dependencies
| | Kya hai | Kaun badalta hai |
|---|---|---|
| Chat history | Jo bola gaya (messages) | Khud save hoti hai |
| Session state | Conversation ka data (dict) | Aap / tools |
| Dependencies | Bahar se fresh data har run pe | Aap ke functions |

## Tool mein state
```python
from agno.run import RunContext

def add_item(run_context: RunContext, item: str) -> str:
    run_context.session_state["cart"].append(item)
```
`run_context` model ko nazar nahi aata — Agno khud deta hai.

## Run
```
uv run python class_04_session_state\01_session_state.py
uv run python class_04_session_state\02_state_with_tools.py
uv run python class_04_session_state\03_dependencies_context.py
```
