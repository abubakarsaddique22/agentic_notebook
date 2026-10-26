# 01 — Setup aur Pehla Trace

## Concepts
- **Trace**: ek user request ka poora safar (start se end tak).
- **Run**: trace ke andar ek step (function call, LLM call, tool call). Runs ek tree banate hain.
- **Project**: traces ka folder. Har app/environment ka alag project hota hai.

```
Trace (root run: "answer_question")
 ├── Run: "retrieve_docs"     (retriever)
 └── Run: "ChatGroq"          (llm)  <- tokens, cost, latency yahan dikhte hain
```

## Files
| File | Kya karti hai |
|---|---|
| `01_check_connection.py` | Check karti hai keys sahi hain aur LangSmith se connect ho raha hai |
| `02_first_trace.py` | Bina LLM ke pehla trace (free) + phir Groq LLM ke saath |

## Chalao
```powershell
python 01_setup_and_first_trace\01_check_connection.py
python 01_setup_and_first_trace\02_first_trace.py
```

## UI mein kya dekhna hai
1. smith.langchain.com → **Tracing Projects** → `langsmith-learning`
2. Trace par click → left side tree, right side **Input / Output**
3. LLM run par click → **tokens, latency, cost** dekho
