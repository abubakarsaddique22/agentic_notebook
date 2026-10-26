# Langfuse — Zero se Industry Level tak

LangSmith ke baad ab **Langfuse**. Structure bilkul LangSmith folder jaisa hai:
har folder **ek concept**, aur aakhri folder (`10_capstone_support_bot`) mein sab concepts ek **real project** mein.

> SDK version: **Langfuse Python SDK v5** (OpenTelemetry-based). Purane tutorials (v2/v3) mein
> `langfuse.trace(...)`, `update_current_trace(...)`, `langfuse_trace_id=` jaisi cheezein hain —
> wo ab **kaam nahi karti**. Is folder ka code naye API par hai.

---

## Langfuse kya hai? (aur LangSmith se farq)

Langfuse bhi LLM apps ke liye **observability + evaluation + prompt management** platform hai.
Bara farq: **open-source (MIT)** hai — apne server par free mein **self-host** kar sakte ho (folder 09).
Isliye bohat companies (khaas kar jinhein data apne paas rakhna hai) Langfuse use karti hain.

### LangSmith ↔ Langfuse concept map (jo tum seekh chuke ho, uska Langfuse naam)

| LangSmith | Langfuse | Note |
|---|---|---|
| `@traceable` | `@observe()` | Same idea |
| `run_type="llm"/"tool"/"retriever"` | `as_type="generation"/"tool"/"retriever"/"agent"/...` | Langfuse mein zyada types |
| Run | **Observation** | Trace ke andar ek step |
| `wrap_openai(OpenAI())` | `from langfuse.openai import OpenAI` | Drop-in import |
| LangChain auto-tracing (env var) | `CallbackHandler()` pass karna parta hai | Langfuse mein explicit |
| `metadata={"thread_id": ...}` → Threads | `propagate_attributes(session_id=...)` → **Sessions** | |
| `user_id` metadata | `propagate_attributes(user_id=...)` → **Users** tab | Langfuse mein built-in |
| Project per env (`app-dev`, `app-prod`) | **Environments** (ek project, `environment="production"`) | |
| `hide_inputs=fn` | `Langfuse(mask=fn)` | |
| `LANGSMITH_TRACING_SAMPLING_RATE` | `LANGFUSE_SAMPLE_RATE` | |
| Dataset + examples | Dataset + **items** | |
| `client.evaluate(...)` → Experiment | `dataset.run_experiment(...)` → **Experiment / Dataset Run** | |
| Feedback (`create_feedback`) | **Scores** (`create_score`) | Scores = feedback + eval results dono |
| Prompt Hub (commits + tags) | Prompt Management (**versions + labels**) | `production` label default |
| Online evaluators | **LLM-as-a-Judge evaluators** (UI) | |
| — | **Self-hosting** (Docker) | Langfuse ka khaas feature |

---

## Folder Roadmap (isi order mein karo)

| # | Folder | Kya seekhoge |
|---|---|---|
| 01 | `01_setup_and_first_trace` | Keys, `auth_check`, pehla trace |
| 02 | `02_tracing_basics` | `@observe`, observation types, OpenAI integration, context managers, errors, async |
| 03 | `03_langchain_langgraph` | `CallbackHandler` ke saath LangChain + LangGraph agent |
| 04 | `04_production_tracing` | environments/release, sessions + users, PII masking, sampling, distributed tracing |
| 05 | `05_datasets` | dataset + items, traces se dataset, versions + archive |
| 06 | `06_evaluation` | `run_experiment`, code evaluators, LLM-as-judge, autoevals, run comparison, pytest |
| 07 | `07_prompt_management` | create/version/label prompts, fallback + cache, prompt ko traces se link karna |
| 08 | `08_scores_and_monitoring` | user feedback scores, metrics API se cost/latency report, UI features |
| 09 | `09_self_hosting` | Docker se apna Langfuse server (Windows) |
| 10 | `10_capstone_support_bot` | **Real project**: FastAPI support bot + sab concepts |

Har folder mein `README.md` hai — pehle wo parho, phir files number order mein chalao.

---

## Setup (Windows)

### 1. Langfuse account + keys
1. https://cloud.langfuse.com par sign up karo (free "Hobby" plan seekhne ke liye kaafi hai)
   - Signup ke waqt **region** chunte ho: EU (`cloud.langfuse.com`) ya US (`us.cloud.langfuse.com`). Yaad rakhna.
2. Organization → Project banao
3. Project → **Settings → API Keys → Create new API keys**
   - `Public Key` (`pk-lf-...`) aur `Secret Key` (`sk-lf-...`) dono copy karo
4. OpenAI key: https://platform.openai.com/api-keys

### 2. Python version — IMPORTANT
Langfuse SDK v5 ko **Python 3.11 ya naya** chahiye. Check karo:
```powershell
python --version
```
3.10 ya purana ho to python.org se 3.12 install karo.

### 3. Virtual environment + packages
LangSmith wala `.venv` mat use karna — yahan alag banao:
```powershell
cd C:\Users\abubakar\Desktop\langfuse
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```
> `Activate.ps1` par error aaye: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` ek dafa chalao.

### 4. `.env` file
```powershell
copy .env.example .env
notepad .env
```
Keys daalo. **US region** wala account hai to `LANGFUSE_BASE_URL=https://us.cloud.langfuse.com` karo.

### 5. Scripts chalana
**Hamesha root folder (`langfuse`) se:**
```powershell
python 01_setup_and_first_trace\01_check_connection.py
```
Har script ke baad https://cloud.langfuse.com → apna project → **Tracing** mein trace dekho.
(Trace aane mein kuch seconds lag sakte hain — SDK background mein batch karke bhejta hai.)

---

## Important Environment Variables

| Variable | Kaam |
|---|---|
| `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY` | Keys |
| `LANGFUSE_BASE_URL` | Region ya self-hosted URL |
| `LANGFUSE_TRACING_ENVIRONMENT` | `development` / `production` — traces filter karne ke liye |
| `LANGFUSE_RELEASE` | App version (e.g. `1.4.0`) |
| `LANGFUSE_SAMPLE_RATE` | Sirf X% traces bhejna (e.g. `0.2`) |
| `LANGFUSE_TRACING_ENABLED` | `false` = tracing band |
| `LANGFUSE_DEBUG` | `True` = SDK ke debug logs (masla aaye to) |

---

## Langfuse ka core data model

```
Session  (ek conversation — session_id)
 └── Trace  (ek request)
      ├── Observation: span        "handle-message"
      │    ├── Observation: retriever  "faq-search"
      │    └── Observation: generation "openai-chat"  <- model, tokens, cost
      └── Scores  (user_rating = 1, correctness = 0.8, ...)
User  (user_id — Users tab mein har user ki cost/usage)
```

## Industry workflow (Langfuse ke saath)

1. Pehle din se tracing (`@observe` + OpenAI/LangChain integration)
2. `environment` + `release` set karo, `user_id` + `session_id` har trace par
3. Prompts code se nikaal kar **Prompt Management** mein (label `production`)
4. User feedback → **scores**
5. Bure traces → **dataset** → prompt fix → **experiment** → compare → `production` label move
6. CI mein experiments (pytest) + production par LLM-as-judge evaluators
