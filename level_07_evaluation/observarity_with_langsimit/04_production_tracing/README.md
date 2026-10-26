# 04 — Production Tracing (Industry Patterns)

Seekhne wale tracing ON kar dete hain bas. Production mein yeh cheezein bhi chahiye:

| Problem | Solution | File |
|---|---|---|
| Dev aur prod ke traces mix ho rahe hain | Har environment ka alag **project** | `01_projects_and_environments.py` |
| Chatbot ki poori conversation ek jagah dekhni hai | **Threads** (`thread_id` / `session_id` metadata) | `02_threads_conversations.py` |
| Phone numbers, emails, addresses LangSmith mein ja rahe hain | **Masking** (`hide_inputs` / `hide_outputs`) | `03_masking_pii.py` |
| Lakhon requests — sab trace karna mehnga | **Sampling rate** | `04_sampling_and_flush.py` |
| Short scripts / serverless mein traces gum | **flush()** | `04_sampling_and_flush.py` |
| Request ek service se doosri mein jati hai (microservices) | **Distributed tracing** (headers) | `05_distributed_tracing.py` |

## Golden rules
1. Project naam: `<app>-<env>` → `support-bot-dev`, `support-bot-prod`
2. Har trace par `user_id`, `thread_id`, `app_version` / `prompt_version` metadata
3. PII kabhi plain text mein mat bhejo
4. Tracing kabhi app ko crash nahi karti — background thread mein bhejti hai (lekin flush yaad rakho)

## UI
- **Threads tab** (project ke andar) → poori conversation ek view mein
- Project → **Monitor** tab → latency, error rate, tokens, cost charts
