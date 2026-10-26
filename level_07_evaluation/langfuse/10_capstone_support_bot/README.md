# 10 — Capstone: Watch Store Support Bot (Langfuse, Industry Style)

LangSmith capstone wala hi bot — lekin poori observability Langfuse par. Dono ko side-by-side
compare karo: concepts same, API alag.

## Architecture
```
 WhatsApp / Web / CLI
        │
        v
  app/api.py  (FastAPI: /chat, /feedback)
        │
        v
  app/bot.py  chat()   @observe "chat-turn"
        │  propagate_attributes(session_id, user_id, tags, version)
        v
        respond()      @observe "support-bot" (chain)
        ├── app/knowledge.py  retrieve()     [retriever]
        ├── app/prompts.py    get_prompt()   [Langfuse prompt, cache 5 min, fallback]
        ├── OpenAI (langfuse.openai)         [generation: tokens, cost, linked prompt version]
        └── score_current_trace("has_context")
                                                   ──>  Langfuse
  /feedback ──> create_score("user_rating", trace_id)    environment = APP_ENV
                                                         release     = APP_VERSION
  evals/run_evals.py ──> dataset "capstone/watch-support-golden" ──> Dataset Runs
```

## Concept → File map
| Concept | Kahan |
|---|---|
| environment + release + masking + sampling (singleton client) | `app/settings.py` |
| `@observe`, observation types | `app/bot.py`, `app/knowledge.py` |
| `propagate_attributes` → Sessions + Users | `app/bot.py` → `chat()` |
| OpenAI drop-in + prompt link | `app/bot.py` → `respond()` |
| Prompt management + cache + fallback | `app/prompts.py` |
| Automatic score + user feedback score | `app/bot.py` |
| trace_id wapas client ko | `app/bot.py`, `app/api.py` |
| shutdown/flush | `app/api.py` lifespan, `scripts/chat_cli.py` |
| Dataset (folder + stable ids + splits) | `evals/create_dataset.py` |
| Experiment: code + LLM-judge + run evaluators | `evals/run_evals.py` |

## Chalao (sab commands **is folder** se)
```powershell
cd C:\Users\abubakar\Desktop\langfuse\10_capstone_support_bot
..\.venv\Scripts\Activate.ps1

# 1) Prompt Langfuse par push (production label) — warna local fallback chalega
python -m app.prompts

# 2) Terminal chat + feedback
python -m scripts.chat_cli

# 3) API server
uvicorn app.api:app --reload
```

Doosre PowerShell window se API test:
```powershell
$r = Invoke-RestMethod -Uri http://127.0.0.1:8000/chat -Method Post -ContentType "application/json" `
     -Body '{"question":"JazzCash se payment ho sakti hai? mera number 03001234567 hai","session_id":"wa-001","user_id":"u-1"}'
$r

Invoke-RestMethod -Uri http://127.0.0.1:8000/feedback -Method Post -ContentType "application/json" `
     -Body ("{`"trace_id`":`"" + $r.trace_id + "`",`"score`":0,`"comment`":`"too long`"}")
```
UI mein trace kholo → phone number `<PHONE>` dikhna chahiye (masking), aur `user_rating = 0` score.

```powershell
# 4) Evals (APP_ENV=development mein)
python -m evals.create_dataset
python -m evals.run_evals --name baseline
python -m evals.run_evals --name baseline --split edge-cases
```

## Exercises (inhe karoge to concept pakka)
1. Langfuse UI (Prompts) mein `watch-support-bot` ka naya version banao ("max 1 sentence"), label `staging` do →
   `.env` mein `BOT_PROMPT_LABEL=staging` → `python -m evals.run_evals --name shorter-prompt` →
   UI mein baseline se **Compare** → behtar ho to `production` label move karo (bina code deploy!)
2. `data/faq.json` mein kisi FAQ ke keywords hata do → `retrieval_accuracy` girta dekho
3. 5 aise sawal poocho jinke jawab FAQ mein nahi → Traces filter `has_context = 0` → yeh tumhare **knowledge gaps** hain
4. UI mein LLM-as-a-Judge evaluator: "Is reply in Roman Urdu?" sirf `support-answer` generations par
5. `.env` mein `APP_ENV=production` → environment filter mein `production`, ~25% traces (sampling)
6. Dashboard banao: cost by model, avg `user_rating`, `has_context` rate — release-wise

## Apne WhatsApp bot mein lagana
Webhook handler se `chat(question, session_id=<customer phone ka hash>, user_id=<customer id>)` call karo.
`trace_id` ko message ke saath store karo — customer feedback de (e.g. 👍 reply) to `record_feedback(trace_id, 1)`.
