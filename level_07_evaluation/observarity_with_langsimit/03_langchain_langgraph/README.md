# 03 — LangChain & LangGraph ki Tracing

## Concept
LangChain / LangGraph mein **koi decorator nahi chahiye**. Sirf `LANGSMITH_TRACING=true`
aur API key set ho — har chain, prompt, LLM, tool, graph node automatically trace hota hai.

Customize karne ke liye `config` dict use hoti hai:
```python
chain.invoke(inputs, config={
    "run_name": "Support Chain",
    "tags": ["v1"],
    "metadata": {"user_id": "u1"},
})
```

`@traceable` aur LangChain ko mix bhi kar sakte ho — sab ek hi trace tree mein aata hai.

## Files
| File | Concept |
|---|---|
| `01_langchain_auto_tracing.py` | prompt \| llm \| parser chain, config se name/tags/metadata, traceable ke saath mix |
| `02_langgraph_agent_tracing.py` | Tools wala LangGraph agent — har node + tool call trace mein |

## UI mein dekho
- LangGraph trace mein har **node** (agent, tools) alag run hai
- Tool run par click karke tool ka input/output dekho
- Trace ki top par **"Waterfall"** view — kaunsa step kitna time le raha hai
