# Class 03 — Short-Term Memory (Sessions)

| File | Concept |
|---|---|
| `01_session_history.py` | **db + session_id + add_history_to_context**, `get_chat_history` |
| `02_multiple_sessions.py` | **Alag sessions** = alag conversations |
| `03_session_summary.py` | **Session summaries**, `read_chat_history`, `search_past_sessions` |

## Memory ki qismein (Agno)
| Qisam | Kya yaad rakhti hai | Class |
|---|---|---|
| Chat history (session) | Is conversation ke messages | 03 |
| Session state | Is conversation ka data (cart, list) | 04 |
| User memory (long-term) | User ke baare mein facts — **har** conversation mein | 05 |

## Run
```
uv run python class_03_short_term_memory\01_session_history.py
uv run python class_03_short_term_memory\02_multiple_sessions.py
uv run python class_03_short_term_memory\03_session_summary.py
```
Database `tmp\class03.db` mein save hoti hai. Saaf karna ho to `tmp` folder delete kar do.
