# LangSmith — Zero se Industry Level tak

Yeh folder LangSmith seekhne ke liye hai. Har folder **ek concept** cover karta hai,
aur aakhri folder (`09_capstone_support_bot`) mein sab concepts ek **real project** mein
use hote hain — bilkul waise jaise company mein hota hai.

> LangSmith complete hone ke baad hum **Langfuse** par jayenge (alag folder).

---

## LangSmith kya hai? (1 minute mein)

Jab tum LLM app banate ho (chatbot, RAG, agent), to 3 sawal hamesha aate hain:

| Sawal | LangSmith ka feature |
|---|---|
| Andar kya ho raha hai? Kaunsa step slow hai? Kitne tokens lage? | **Tracing / Observability** |
| Mera naya prompt purane se behtar hai ya bura? | **Datasets + Evaluation (Experiments)** |
| Prompts code se bahar kaise manage karoon, version kaise karoon? | **Prompt Hub** |
| Users khush hain? Production mein kya toot raha hai? | **Feedback + Monitoring** |

---

## Folder Roadmap (isi order mein karo)

| # | Folder | Kya seekhoge |
|---|---|---|
| 01 | `01_setup_and_first_trace` | API key, env vars, pehla trace |
| 02 | `02_tracing_basics` | `@traceable`, `wrap_openai`, run types, metadata, tags, errors, async |
| 03 | `03_langchain_langgraph` | LangChain / LangGraph ki automatic tracing |
| 04 | `04_production_tracing` | projects per environment, threads (conversations), PII masking, sampling, distributed tracing |
| 05 | `05_datasets` | datasets banana, traces se dataset, splits, versioning |
| 06 | `06_evaluation` | code evaluators, LLM-as-judge, summary evaluators, experiments compare, pytest evals |
| 07 | `07_prompt_management` | Prompt Hub — push, pull, versions/tags |
| 08 | `08_feedback_and_monitoring` | user feedback (thumbs up/down), runs query karna, cost/latency analytics |
| 09 | `09_capstone_support_bot` | **Real project**: FastAPI support bot + tracing + feedback + evals |

Har folder mein ek `README.md` hai — pehle wo parho, phir files number order mein chalao.

---

## Setup (Windows)

### 1. LangSmith account + API key
1. https://smith.langchain.com par sign up karo (free plan kaafi hai seekhne ke liye)
2. **Settings → API Keys → Create API Key** — key `lsv2_...` se shuru hogi
3. Groq API key bhi chahiye: https://console.groq.com/keys  (.env mein GROQ_API_KEY)

### 2. Virtual environment + packages
(Python **3.10 ya naya** chahiye — `python --version` se check karo.)

Is folder mein terminal (PowerShell) kholo:

```powershell
cd C:\Users\abubakar\Desktop\langsimit
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

> Agar `Activate.ps1` par error aaye: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` ek dafa chalao.

### 3. `.env` file
`.env.example` ko copy karke `.env` banao aur apni keys daalo:

```powershell
copy .env.example .env
notepad .env
```

### 4. Scripts kaise chalani hain
**Hamesha root folder (`langsimit`) se** chalao:

```powershell
python 01_setup_and_first_trace\01_check_connection.py
python 02_tracing_basics\01_traceable_decorator.py
```

Har script ke baad https://smith.langchain.com par jao → apna project kholo → trace dekho.
**Trace dekhna hi asal seekhna hai** — code sirf aadha hai.

---

## Important Environment Variables

| Variable | Kaam |
|---|---|
| `LANGSMITH_TRACING=true` | Tracing ON/OFF ka main switch |
| `LANGSMITH_API_KEY` | Tumhari key |
| `LANGSMITH_PROJECT` | Traces kis project mein jayein (default: `default`) |
| `LANGSMITH_ENDPOINT` | Sirf EU region ya self-hosted ke liye change karna |
| `LANGSMITH_TRACING_SAMPLING_RATE` | Production mein sirf X% traces bhejna (e.g. `0.1`) |
| `LANGSMITH_HIDE_INPUTS` / `LANGSMITH_HIDE_OUTPUTS` | Inputs/outputs bilkul chhupana |

---

## Industry mein LangSmith ka typical workflow

```
 Build app ──> Trace everything ──> Production traces dekho
     ^                                     │
     │                                     v
 Prompt/model change  <── Experiment <── Bure/achhe traces ko Dataset mein daalo
 (Prompt Hub)            (evaluate)        + User feedback
```

1. **Tracing** pehle din se ON
2. Har environment ka alag project (`myapp-dev`, `myapp-prod`)
3. Production ke interesting traces → **dataset**
4. Har prompt/model change se pehle → **experiment** chalao, purane se compare karo
5. User feedback trace ke saath attach karo
6. CI mein evals (pytest) taake regression pakra jaye
