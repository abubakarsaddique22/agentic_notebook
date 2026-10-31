# Class 06 — Structured Output aur Reasoning

| File | Concept |
|---|---|
| `01_output_schema.py` | **output_schema** — jawab Pydantic object |
| `02_input_schema.py` | **input_schema** — input ka fix format + validation |
| `03_reasoning.py` | **ReasoningTools** (think/analyze) + **reasoning_model** |

## Yaad rakho
```python
agent = Agent(model=..., output_schema=MyModel)
result = agent.run("...")
result.content.field_name      # object hai, string nahi
```

## Reasoning kab use karein
- Math / budget calculation
- Multi-step planning
- Comparison ("A vs B")
Simple sawalon pe mat lagao — zyada tokens aur time lagta hai.

## Run
```
uv run python class_06_structured_output_reasoning\01_output_schema.py
uv run python class_06_structured_output_reasoning\02_input_schema.py
uv run python class_06_structured_output_reasoning\03_reasoning.py
```
