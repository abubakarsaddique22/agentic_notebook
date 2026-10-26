# 01 — Setup aur Pehla Trace

## Concepts
- **Trace**: ek request ka poora record (start se end tak).
- **Observation**: trace ke andar ek step. Types: `span` (general), `generation` (LLM call), `tool`, `retriever`, `agent` wagera.
- **Project**: Langfuse mein ek app = ek project. Environments (dev/prod) project ke **andar** filter hote hain.
- Langfuse SDK **OpenTelemetry** par bana hai — observations background mein batch karke bheje jate hain.
  Isliye chhoti scripts ke end par `langfuse.flush()` zaroor karo.

```
Trace
 └── span: "checkout"
      └── span: "add_tax"            <- nested (child)
```

## Files
| File | Kya karti hai |
|---|---|
| `01_check_connection.py` | Keys check + `auth_check()` |
| `02_first_trace.py` | Bina LLM (free) + OpenAI ke saath pehla trace |

## Chalao
```powershell
python 01_setup_and_first_trace\01_check_connection.py
python 01_setup_and_first_trace\02_first_trace.py
```

## UI mein kya dekhna hai
1. cloud.langfuse.com → project → **Tracing → Traces**
2. Trace kholo → left side observation tree, right side **Input / Output**
3. Generation (OpenAI) par click → **model, tokens, cost, latency**
