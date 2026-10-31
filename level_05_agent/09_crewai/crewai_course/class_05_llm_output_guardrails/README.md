# Class 05 — LLMs, Structured Output aur Guardrails

| File | Concept |
|---|---|
| `01_llm_config.py` | **LLM class** — direct `llm.call()`, temperature, har agent ka alag LLM |
| `02_structured_output.py` | **Structured output** — `output_pydantic`, `output_json` |
| `03_guardrails.py` | **Guardrails** — function guardrail + LLM (text) guardrail + retries |

## Guardrail ka flow
```
Agent jawab deta hai
      │
      ▼
 Guardrail check ──Pass──▶ agla task / final result
      │
     Fail (feedback)
      │
      ▼
 Agent dobara likhta hai  (guardrail_max_retries tak)
```

## Function guardrail ka format (yaad kar lo)
```python
def my_check(output: TaskOutput):
    if <kuch galat>:
        return (False, "agent ke liye feedback")
    return (True, output.raw)
```

## Structured output
```python
Task(..., output_pydantic=MyModel)   ->  result.pydantic.field_name
Task(..., output_json=MyModel)       ->  result.json_dict["field_name"]
```

## Run
```
uv run python class_05_llm_output_guardrails\01_llm_config.py
uv run python class_05_llm_output_guardrails\02_structured_output.py
uv run python class_05_llm_output_guardrails\03_guardrails.py
```

## Practice
- Guardrail banao jo check kare ke caption mein "PKR" price likha ho.
- `ProductListing` mein `category: str` field add karo.
