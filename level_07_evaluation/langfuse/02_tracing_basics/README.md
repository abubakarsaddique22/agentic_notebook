# 02 — Tracing Basics (sabse important folder)

## Concepts

### 1. `@observe()` decorator
Kisi bhi function par lagao → wo ek **observation** ban jata hai. Andar wale `@observe` functions **children** bante hain.
Sab se bahar wala function **trace** ka root hota hai.

```python
@observe(name="my-step", as_type="tool", capture_input=True, capture_output=True)
```

### 2. Observation types (`as_type`)
| as_type | Kab use karo |
|---|---|
| `span` (default) | General step / pipeline |
| `generation` | LLM call (model, tokens, cost) |
| `agent` | Agent jo decide karta hai kaunsa tool chalana hai |
| `tool` | Agent ka tool (DB query, API call, calculator) |
| `retriever` | RAG mein documents nikalna |
| `chain` | Steps ko jorne wala logic |
| `embedding` | Embedding model call |
| `evaluator` | Output ko grade karna |
| `guardrail` | Jailbreak / harmful content check |

### 3. Running observation ko update karna
- `langfuse.update_current_span(metadata=..., level="WARNING", status_message=...)`
- `langfuse.update_current_generation(model=..., usage_details=..., cost_details=...)`

### 4. Trace attributes — `propagate_attributes()`
`user_id`, `session_id`, `tags`, `metadata`, `version`, `trace_name` — yeh is context ke andar banne wali **har** observation par lagte hain.
> v3 ka `update_current_trace()` ab **nahi hai**. Uski jagah `propagate_attributes()`.

### 5. OpenAI drop-in
`from langfuse.openai import OpenAI` — baqi code same. Extra kwargs: `name=`, `metadata=`, `langfuse_prompt=`.

### 6. Context managers
Jab decorator nahi laga sakte: `with langfuse.start_as_current_observation(as_type="span", name=...) as span:`

## Files (order mein)
| File | Concept |
|---|---|
| `01_observe_decorator.py` | nesting, name, as_type, capture_input/output, update_current_span |
| `02_openai_integration.py` | drop-in client, name/metadata kwargs, streaming, JSON output |
| `03_context_managers_and_attributes.py` | `start_as_current_observation`, `propagate_attributes`, trace_id/URL |
| `04_observation_types.py` | retriever/tool/agent/generation + khud ka LLM (manual tokens/cost) |
| `05_errors_and_async.py` | errors (level ERROR), warnings, async + parallel |

## UI Exercise
- Traces list mein **Filter** → `Tags` = `v2`
- `Users` tab → `user_123` ki usage/cost
- Error wali observation (laal) kholo → status message dekho
