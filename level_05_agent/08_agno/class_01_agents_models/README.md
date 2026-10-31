# Class 01 — Agents aur Models

| File | Concept |
|---|---|
| `01_first_agent.py` | **Agent + Model**, `print_response`, `stream`, `markdown` |
| `02_instructions_and_run.py` | `description`, `instructions`, `expected_output`, `additional_context`, **`run()` → RunOutput** |
| `03_multiple_models.py` | Groq / OpenRouter / Ollama / Gemini + **fallback_models** |

## Yaad rakho
```python
agent = Agent(model=..., instructions=[...], markdown=True)
agent.print_response("sawal", stream=True)   # sirf dikhana
result = agent.run("sawal")                  # code mein use karna
result.content                               # jawab
```

## Problem (agli class ki taraf)
Ye agent **tools** ke baghair sirf apni training se jawab deta hai — aaj ki khabar, calculator, database kuch nahi. Class 02 mein tools dete hain.

## Run
```
uv run python class_01_agents_models\01_first_agent.py
uv run python class_01_agents_models\02_instructions_and_run.py
uv run python class_01_agents_models\03_multiple_models.py
```
