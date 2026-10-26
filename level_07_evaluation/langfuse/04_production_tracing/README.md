# 04 — Production Tracing (Industry Patterns)

| Problem | Langfuse solution | File |
|---|---|---|
| Dev aur prod traces mix | **Environments** (`LANGFUSE_TRACING_ENVIRONMENT`) + **release** | `01_environments_and_release.py` |
| Chatbot ki poori conversation + har user ka hisaab | **Sessions** (`session_id`) + **Users** (`user_id`) | `02_sessions_and_users.py` |
| Phone/email/CNIC Langfuse mein ja rahe hain | **Masking** (`Langfuse(mask=fn)`) | `03_masking_pii.py` |
| Lakhon requests — sab trace karna mehnga | **Sampling** (`sample_rate`) | `04_sampling_and_flush.py` |
| Scripts / serverless mein traces gum | **`flush()`** | `04_sampling_and_flush.py` |
| Request ek service se doosri mein (microservices) | **Distributed tracing** (`trace_context`) | `05_distributed_tracing.py` |

## LangSmith se farq
- LangSmith: har environment ka **alag project** (`app-dev`, `app-prod`)
- Langfuse: **ek project**, traces par `environment` tag. UI mein top par environment dropdown.
  (Chaho to alag projects bhi bana sakte ho — badi teams karti hain — lekin environments simple hain.)

## Golden rules
1. `environment` + `release` (app version) har deployment par set
2. Har trace par `user_id` + `session_id`
3. PII kabhi plain text mein nahi
4. Short scripts / workers / serverless: end par `langfuse.flush()` (FastAPI jaisa server: shutdown par)
5. Langfuse client **singleton** hai — config wala `Langfuse(...)` app start par **sabse pehle** banao,
   baad mein har jagah `get_client()` wahi config wala client deta hai

## UI
- Top bar → **Environment** filter
- **Sessions** tab → poori conversation
- **Users** tab → har user ki traces, tokens, cost
- **Dashboards** → latency, cost, errors (release / environment wise)
