# 09 — Capstone: Watch Store Support Bot (Industry Style)

Yeh folder dikhata hai ke **real project mein LangSmith kaise lagta hai** — alag scripts nahi,
balke ek structured app jahan observability, evals, prompts aur feedback sab built-in hain.

## Architecture
```
 WhatsApp / Web / CLI
        │
        v
  app/api.py  (FastAPI: /chat, /feedback)
        │
        v
  app/bot.py  chat()  ── run_id + thread_id + user_id + app_version ──┐
        │                                                             │
        ├── app/knowledge.py  retrieve()        [retriever run]       │  LangSmith
        ├── app/prompts.py    get_prompt()      [Prompt Hub/fallback] ├─> project:
        └── Groq (wrap_openai)                  [llm run: tokens/cost]│  watch-support-bot-<env>
                                                                      │  (PII masked)
  /feedback ──> record_feedback(run_id)  ─────────────────────────────┘

  evals/run_evals.py ──> dataset "watch-support-bot-golden" ──> Experiments
```

## Concept → File map
| Concept | Kahan |
|---|---|
| Project per environment, sampling in prod | `app/settings.py` |
| PII masking (phone/email) | `app/settings.py` → `ls_client` |
| `@traceable`, `wrap_openai`, runtime metadata/tags | `app/bot.py` |
| Retriever run type | `app/knowledge.py` |
| Prompt Hub + cache + fallback | `app/prompts.py` |
| Threads (`thread_id`) | `app/bot.py` → `chat()` |
| run_id control + user feedback | `app/bot.py`, `app/api.py` `/feedback` |
| Flush on shutdown | `app/api.py` lifespan, `scripts/chat_cli.py` |
| Golden dataset + splits | `evals/create_dataset.py` |
| Code + LLM-judge + summary evaluators, experiments | `evals/run_evals.py` |

## Chalao (sab commands **is folder** se)
```powershell
cd C:\Users\abubakar\Desktop\langsimit\09_capstone_support_bot
..\.venv\Scripts\Activate.ps1

# 1) (Optional) Prompt hub par push — warna local prompt chalega
python -m app.prompts

# 2) Terminal chat + feedback
python -m scripts.chat_cli

# 3) API server
uvicorn app.api:app --reload
```

Doosre PowerShell window se API test:
```powershell
$r = Invoke-RestMethod -Uri http://127.0.0.1:8000/chat -Method Post -ContentType "application/json" `
     -Body '{"question":"JazzCash se payment ho sakti hai? mera number 03001234567 hai","thread_id":"wa-001","user_id":"u-1"}'
$r

Invoke-RestMethod -Uri http://127.0.0.1:8000/feedback -Method Post -ContentType "application/json" `
     -Body ("{`"run_id`":`"" + $r.run_id + "`",`"score`":0,`"comment`":`"too long`"}")
```
UI mein trace kholo → phone number `<PHONE>` dikhna chahiye (masking).

```powershell
# 4) Evals
python -m evals.create_dataset
python -m evals.run_evals --name baseline
python -m evals.run_evals --name baseline --split edge-cases
```

## Exercises (inhe karoge to concept pakka)
1. `app/prompts.py` mein rule badlo (e.g. "max 1 sentence") → `--name shorter-prompt` se evals → UI mein baseline se **Compare**
2. `data/faq.json` mein ek FAQ ke keywords hata do → `retrieval_accuracy` girta dekho
3. 5 sawal poocho jinke jawab FAQ mein nahi → project mein tag `no-context` se filter → yeh tumhare **knowledge gaps** hain
4. UI mein Automation Rule: `user_rating = 0` → dataset `bad-replies`
5. `.env` mein `APP_ENV=prod` → traces `watch-support-bot-prod` mein (25% sampling)
6. Hub par prompt ke latest commit par `prod` tag lagao, `.env` mein `BOT_PROMPT_ID=watch-support-bot-prompt:prod`

## Apne WhatsApp bot mein lagana
`chat(question, thread_id=<customer phone hash>, user_id=<customer id>)` ko apne webhook handler se call karo.
`thread_id` ke liye phone number ka hash use karo (raw number nahi) — masking ke ilawa extra safety.
