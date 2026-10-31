# Class 08 — Guardrails aur Hooks

| File | Concept |
|---|---|
| `01_builtin_guardrails.py` | **PromptInjectionGuardrail, PIIDetectionGuardrail** (block + mask + Pakistani patterns) |
| `02_custom_guardrail.py` | **Custom input guardrail** (`BaseGuardrail`) + **output guardrail** (`post_hooks`) |
| `03_pre_post_hooks.py` | **pre_hooks / post_hooks** — logging, input saaf karna, output badalna |
| `04_tool_hooks.py` | **tool_hooks** — har tool call ka middleware, tool block karna |

## Kahan kya lagta hai
```
User input ─▶ [pre_hooks / guardrails] ─▶ Model ─▶ [tool_hooks] ─▶ Tool
                                            │
                                            ▼
                               [post_hooks / output guardrails] ─▶ User
```

## Guardrail fail hone pe
Exception bahar nahi aata. `result.status` = error aur `result.content` = wajah.

## Run
```
uv run python class_08_guardrails_hooks\01_builtin_guardrails.py
uv run python class_08_guardrails_hooks\02_custom_guardrail.py
uv run python class_08_guardrails_hooks\03_pre_post_hooks.py
uv run python class_08_guardrails_hooks\04_tool_hooks.py
```
