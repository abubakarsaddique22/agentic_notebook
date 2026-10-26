# Level 9 · AI System Design

> **Goal:** Ek production AI application design karna aur har architectural choice ko **defend** karna:
> quality, latency, cost, reliability aur user experience ke hisaab se.
>
> **Do outcomes:**
> 1. **Job / interview:** "Design a chatbot over company docs" jaisa system-design round confidence se clear karna.
> 2. **Freelancing:** Client ka project akele scope karna, cost bata dena, architecture choose karna, aur build karna.

---

## Ye level pichle levels se alag kyun hai?

| Level 0–8 mein aap ne seekha | Level 9 mein aap seekhenge |
|---|---|
| RAG kaise banta hai | RAG **kab** chahiye, aur kab nahi |
| Agent kaise banta hai | Agent banana chahiye ya simple pipeline kaafi hai |
| Evals kaise chalate hain | Evals ko production loop mein kahan fit karna hai |
| Security attacks/defences | Guardrails system ki kis boundary par lagane hain |
| Ek model call karna | Kaun sa model, kab, fallback kya, cost kitni |

**Short mein:** pehle aap ne **bricks** banana seekha. Ab **building ka naqsha** banana seekhna hai.

---

## Modules (sab ✅ ready)

| # | Folder | Topic | Main files | Run (offline) |
|---|---|---|---|---|
| M9.1 | `01_design_framework` | Requirements → baseline, prompting vs RAG vs agent vs fine-tune, trade-offs | `notes.md`, `cost_latency_estimator.py`, `measure_baseline.py` | `python 01_design_framework\cost_latency_estimator.py` |
| M9.2 | `02_context_knowledge` | Knowledge sources, context pipeline, hybrid, freshness, ACL, provenance | `knowledge_pipeline.py` | `python 02_context_knowledge\knowledge_pipeline.py --offline` |
| M9.3 | `03_model_routing_gateway` | Gateway, routing, cascades, fallbacks, budgets | `gateway.py` (LiteLLM) | `python 03_model_routing_gateway\gateway.py --mock` |
| M9.4 | `04_latency_optimization` | TTFT, streaming, parallel, context size, capacity math | `latency_lab.py` | `python 04_latency_optimization\latency_lab.py --mock` |
| M9.5 | `05_caching` | Exact / semantic / retrieval / prompt cache, invalidation, hit rate | `caching_lab.py` | `python 05_caching\caching_lab.py --offline` |
| M9.6 | `06_reliability_guardrails` | Retries, timeouts, circuit breaker, guards, degradation, SLOs | `reliability.py` | `python 06_reliability_guardrails\reliability.py` |
| M9.7 | `07_pipeline_orchestration` | Deterministic vs model decisions, sync/async/jobs, boundaries | `app.py`, `components.py`, `try_app.py` | `python 07_pipeline_orchestration\try_app.py` |
| M9.8 | `08_monitoring_feedback` | Tracing, feedback, versioning, regressions, failures → evals | `monitoring_lab.py`, `tracer.py`, `langfuse_tracing.py` | `python 08_monitoring_feedback\monitoring_lab.py` |
| M9.9 | `09_case_studies` | Support copilot, coding assistant, deep research agent | `00_how_to_whiteboard.md` + 3 cases | (notes only) |
| M9.10 | `10_capstone_design_doc` | Full design doc: WhatsApp support bot + reusable template | `whatsapp_support_bot_design.md`, `design_doc_template.md` | (doc) |

**Extra:**
- `CHEATSHEET.md`: poora level 1 page mein (interview se pehle revise karo)
- `GLOSSARY.md`: saare terms
- `templates/requirements_template.md`: client discovery call form
- `run_all_offline.py`: saare scripts ek saath chala kar setup check karta hai
- `shared/embeddings.py`: Ollama embeddings + offline fallback (M2, M5 use karte hain)

## Har module mein

- `notes.md`: simple samjhao → diagrams → decision tables → industry → mistakes → **freelance lens** → interview Q&A → summary
- `exercise.md`: code modify karne wale tasks + design practice
- Code: **har script offline (mock) chalti hai**, aur `.env` mein key ho to real Groq bhi

---

## Setup (Windows, ek dafa)

PowerShell mein `ai_system_design` folder ke andar:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```
Phir `.env` file kholein aur `GROQ_API_KEY` daal dein (real mode ke liye; offline ke liye zaroori nahi).

```powershell
# Sab kuch theek install hua? (koi API key nahi chahiye)
python run_all_offline.py
```

> Agar `Activate.ps1` par "running scripts is disabled" error aaye: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`
> Agar output mein emoji / boxes par `UnicodeEncodeError` aaye: `$env:PYTHONIOENCODING="utf-8"`

**Optional:**
- Real embeddings (M2, M5): Ollama chalu rakhein aur `ollama pull nomic-embed-text`
- Langfuse (M8): free account, keys `.env` mein (`langfuse_tracing.py` ke upar steps)

### Mermaid diagrams dekhna (VS Code)
Extension install karein: **"Markdown Preview Mermaid Support"** (by Matt Bierner). Phir `notes.md` kholein aur `Ctrl+Shift+V` dabayein.

---

## Stack (sab free / free tier)

| Kaam | Tool | Module |
|---|---|---|
| Main LLM | **Groq** (`openai/gpt-oss-20b`, `openai/gpt-oss-120b`) | Sab |
| Local fallback + embeddings | **Ollama** | M2, M3, M5 |
| Model gateway / router | **LiteLLM** | M3 |
| Vector DB | **Chroma** | M2 |
| Keyword search | **rank-bm25** | M2 |
| Cache | **diskcache** (production mein Redis) | M5 |
| Retries | **tenacity** | M6 |
| Output validation | **pydantic** | M6 |
| API / jobs | **FastAPI** | M7 |
| Tracing + feedback | SQLite tracer + **Langfuse** | M8 |

---

## Kaise parhna hai (recommended order)

1. Module ki `notes.md` poori parhein.
2. Script offline chalayein, output dekhein, phir real mode.
3. `exercise.md` khud karein (likh kar / code badal kar).
4. Interview questions ke answers pehle **khud bolein**, phir model answer se compare karein.
5. Output / sawal mujhe share karein.
6. Aakhir mein **capstone** (`10_capstone_design_doc`) ko apne real data se complete karein. Yahi Level 9 ka "Ship it" hai.

**Suggested pace:** ~2 modules per week → 5 hafte. M9.9 aur M9.10 par sab se zyada waqt dein.

## Main reference
- **Chip Huyen: *AI Engineering*** (O'Reilly). Chapter 10 (AI Engineering Architecture and User Feedback) khaas taur par.
- Anthropic: *Building effective agents* (workflows vs agents, M9.7)
