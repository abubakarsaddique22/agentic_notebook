# 03 — LangChain & LangGraph ke saath Langfuse

## Concept (LangSmith se farq)
LangSmith mein LangChain **khud** trace hota tha (env var se). Langfuse mein ek **`CallbackHandler`**
pass karna parta hai:

```python
from langfuse.langchain import CallbackHandler
handler = CallbackHandler()
chain.invoke(inputs, config={"callbacks": [handler]})
```

Trace attributes do tareeqon se:
1. **metadata keys** (sirf LangChain ke liye):
   `langfuse_user_id`, `langfuse_session_id`, `langfuse_tags`, `langfuse_trace_name`
2. **`propagate_attributes()`** — jab chain kisi `@observe` function ke andar ho (recommended, sab integrations ke saath kaam karta hai)

`@observe` function ke andar `CallbackHandler()` banao → LangChain ki observations usi trace mein nest ho jati hain.

## Files
| File | Concept |
|---|---|
| `01_langchain_callback.py` | prompt \| llm \| parser chain, metadata keys, @observe ke andar chain |
| `02_langgraph_agent.py` | Tools wala LangGraph agent — har node + tool call trace mein |

## UI
- LangGraph trace mein har **node** (agent, tools) alag observation
- **Agent Graph** view (trace ke upar) — graph ki shakal mein flow
- Tool observation kholo → input/output
