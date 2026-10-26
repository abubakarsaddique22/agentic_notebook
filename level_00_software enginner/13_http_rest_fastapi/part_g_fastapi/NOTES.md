# PART G: ⚡ FastAPI

Ab tak aap **client** the. Ab **server** banate hain.

Har file ko do tareeqon se chala sakte hain:
```
python -m part_g_fastapi.g03_path_query_params                      ← TestClient demo (bina server)
uvicorn part_g_fastapi.g03_path_query_params:app --reload --port 8000  ← asli server, browser mein /docs
```
`TestClient` app ko **bina server ke** seedha call karta hai, API `httpx` jaisi hai. Tests mein bhi yahi use hota hai.

## G.1 FastAPI kya hai aur kyun?
FastAPI Python ka modern web framework hai jo **Starlette** (web/async hissa) aur **Pydantic** (validation) ke upar bana hai.

| Khoobi | Fayda |
|---|---|
| **Type hints = validation** | `qty: int` likha, aur ghalat data par khud 422 |
| **Auto docs** | `/docs` (Swagger) aur `/redoc` khud bante hain |
| **Async support** | LLM/API calls ka intezar karte hue doosri requests handle |
| **Dependency Injection** | Auth, DB, settings ek jagah |
| **Tez** | Python frameworks mein sab se tez frameworks mein se |
| **AI ka standard** | Zyada tar LLM apps, RAG APIs aur model serving FastAPI par |

| | Flask | Django | **FastAPI** |
|---|---|---|---|
| Kism | Micro, WSGI | Full stack (admin, ORM), WSGI/ASGI | API-first, **ASGI** |
| Validation | Khud/extension | Forms/DRF serializers | **Built-in (Pydantic)** |
| Async | Mehdood | Hai, lekin poori tarah nahi | **Native** |
| Docs | Extension | DRF extension | **Built-in** |
| Kab | Chhoti apps, purana code | Bari websites, admin panel | **APIs, AI/ML services** |

> 🎤 **WSGI vs ASGI:** WSGI (purana standard) ek request ek thread mein, sirf sync. **ASGI** async support karta hai, WebSockets aur streaming ke saath. FastAPI ASGI hai, is liye **uvicorn** (ASGI server) se chalta hai.

## G.2 Pehli app
```python
from fastapi import FastAPI
app = FastAPI()

@app.get("/")
def home():
    return {"message": "Salam"}
```
```
uvicorn main:app --reload     # development (code badlo, server khud restart)
fastapi dev main.py           # naya tareeqa (same kaam)
```
`main:app` ka matlab: `main.py` file ke andar `app` variable. Package ke andar file ho to dots: `part_g_fastapi.g02_first_app:app`.

▶ `g02_first_app.py`

## G.3 Path & Query parameters (types = validation)
- Function ke argument ka naam URL ke `{...}` mein hai → **path param**
- Baqi simple types → **query param**
- Default value hai → optional, nahi hai → required
- `Annotated[int, Query(ge=1, le=100)]` → extra validation (ye modern tareeqa hai)
- `Literal["watches", "wallets"]` → sirf ye values allowed

▶ `g03_path_query_params.py`

## G.4 Request body + Response model
- **Request body:** Pydantic model ka argument → FastAPI JSON body parse + validate karta hai
- **`response_model`:** jawab ki **shape** tay karta hai. Faalto/secret fields **khud nikal jaate hain** (jaise password, internal notes)
- **`status_code=201`:** create ke liye

Ye pattern bohat aham hai: **`XxxIn`** (jo client bhejta hai), **`XxxOut`** (jo client ko milta hai), aur andar ka poora data alag.

▶ `g04_body_response_model.py`

## G.5 Errors: ek jaisa format, aur stack trace kabhi bahar nahi
Teen handlers lagate hain:
1. `HTTPException` (404, 401 waghera) → hamara format. Starlette wala class lein taake **route not found** wala 404 bhi pakra jaye
2. `RequestValidationError` (422) → saaf field-wise errors
3. `Exception` (koi bhi crash) → `500` + generic message, aur **poori detail sirf logs mein**

▶ `g05_error_handlers.py`

## G.6 Dependency Injection (`Depends`)
**Dependency** = ek function jo endpoint se **pehle** chalta hai aur kuch **deta** hai (current user, DB session, settings, pagination), ya request **rok** deta hai (auth fail).

Fayde:
- Auth/pagination ka code **ek jagah**, har endpoint mein copy nahi
- Dependencies doosri dependencies use kar sakti hain (chain)
- **Tests mein badal sakte hain** (`app.dependency_overrides`): fake DB, fake LLM

▶ `g06_dependencies.py`

## G.7 `APIRouter`: bari app ko files mein baantna
Har feature ka apna router (file), phir `main.py` mein `app.include_router(router, prefix="/v1")` se jor dein. Router level par `dependencies=[Depends(auth)]` lagao to us ke saare endpoints protected. Part H mein poora structure hai.

▶ `g07_routers.py`

## G.8 Sync vs Async: sab se aham concept (aur interview favorite) 🎤

| Endpoint | FastAPI kahan chalata hai | Kab use karein |
|---|---|---|
| `def` | **Thread pool** mein (alag thread) | Blocking code: `requests`, purani DB library, `time.sleep`, CPU kaam |
| `async def` | **Event loop** par (main thread) | Sirf jab andar `await` wali libraries hon: `httpx.AsyncClient`, `asyncpg`, async LLM SDK |

### ⚠️ Sab se bari ghalti
`async def` ke andar **blocking** code (`time.sleep`, `requests.get`, sync OpenAI client) → **poora server ruk jata hai**, kyun ke event loop ek hi hai aur wo intezar mein phansa hai.

Demo ka natija:
- `/sync-def` ≈ 1s ✅: FastAPI ne har request alag thread mein chalayi
- `/async-bad` ≈ **5s** ❌: event loop par `time.sleep` ne sab ko line mein laga diya. 100 users hon to 100 second!
- `/async-good` ≈ 1s ✅: `await` ke dauraan event loop doosri requests le leta hai

**Rule of thumb:**
1. Andar `await` hai → `async def`
2. Blocking library hai aur async version nahi → `def` (ya `await asyncio.to_thread(blocking_fn)`)
3. **CPU heavy kaam** (model inference, bari image processing) → `def`, ya alag worker (Celery/RQ). Async CPU kaam tez nahi karta, sirf **intezar** ke waqt doosre kaam karta hai

> 🎤 **Concurrency vs Parallelism:** Async = **concurrency** (ek bawarchi kai handiyan dekhta hai, jab ek pak rahi ho to doosri). **Parallelism** = kai bawarchi (multiple processes/CPU cores). I/O bound kaam ke liye async, CPU bound ke liye multiprocessing.

▶ `g08_sync_vs_async.py` (ye khud ek server port 8766 par chala kar test karti hai)

## G.9 Settings (`.env`) + Lifespan + Non-blocking external calls
- **`pydantic-settings`:** `.env` aur environment variables se settings, type validation ke saath. API key `SecretStr` mein ho, taake print/log mein na dikhe
- **Lifespan:** app **shuru** hote waqt ek baar kaam (shared `httpx.AsyncClient` banana, model load, DB connect), aur **band** hote waqt saaf karna
- **Shared async client** se doosri service (yahan practice server, asal mein Shopify/LLM) ko non-blocking call
- **Upstream ki ghalti ka tarjuma:** timeout → 504, pohanch nahi → 502, upstream 5xx → 502
- **Tests mein mock:** `httpx.MockTransport` se nakli server, phir `dependency_overrides`

Is folder mein `.env` file hai (practice values). `.env.example` git mein jata hai, `.env` nahi.

▶ `g09_settings_lifespan.py` (catalog wale hisse ke liye practice server bhi chalayein)

## G.10 Middleware: har request se pehle/baad chalne wala code
Kaam: request ID, timing, logging, CORS, auth headers, rate limiting.
```
Request → [Middleware: start timer] → Endpoint → [Middleware: time likho, header lagao] → Response
```

### CORS (interview mein zaroor poocha jata hai) 🎤
Browser security: `https://mystore.com` ka JavaScript `https://api.other.com` ko call kare to browser **tab tak jawab nahi dikhata** jab tak server `Access-Control-Allow-Origin` header se ijazat na de. Ye **sirf browsers** mein hota hai. Python/curl par CORS lagu nahi hota. Aap ki API ko frontend (React/website) call kare to `CORSMiddleware` lagana parta hai.

▶ `g10_middleware_cors.py`

## G.11 🤖 Webhook endpoint: WhatsApp bot jaisa (real kaam)
Webhook = **doosri service aap ke server ko call karti hai** jab kuch hota hai (naya WhatsApp message, Shopify order, payment). Is mein chaar cheezein zaroori hain:

1. **Verification (GET):** Meta setup ke waqt `hub.challenge` bhejta hai, aap wapas karte hain (agar verify token sahi ho)
2. **Signature check:** header `X-Hub-Signature-256` mein body ka **HMAC-SHA256** hota hai (app secret se). Is se pata chalta hai ke request **waqai WhatsApp se aayi**, kisi hacker se nahi
3. **Dedupe (idempotency):** same `message_id` dobara aaye to ignore
4. **Jaldi `200` lautao:** LLM ka kaam **background** mein karo. Webhook senders kuch second mein jawab na milne par **retry** karte hain (aur phir duplicates aate hain)

> Simplified payload hai. Asli Meta payload nested hota hai (`entry[0].changes[0].value.messages[0]`). Pattern bilkul yahi hai. Production mein background kaam ke liye queue (Redis/Celery/RQ) zyada mazboot hai, kyun ke `BackgroundTasks` server restart par kaam kho deta hai.

> 🎤 `hmac.compare_digest` kyun, `==` kyun nahi? `==` pehla ghalat character milte hi ruk jata hai, is liye **time** mein farq aata hai, aur hacker us farq se signature andaaza laga sakta hai (**timing attack**). `compare_digest` hamesha barabar waqt leta hai.

▶ `g11_whatsapp_webhook.py`

## G.12 🌊 Streaming LLM response (`StreamingResponse`)
Apni API se ChatGPT jaisa token-by-token jawab. Generator `yield` karta hai, aur FastAPI har tukra foran bhejta hai. `media_type="text/event-stream"`.

▶ `g12_streaming.py`

## G.13 Testing with `TestClient` + pytest
Har G file ke `__main__` block mein `TestClient` se test ho raha hai. Asal project mein yahi `tests/` folder mein pytest ke saath hota hai, aur LLM ko `dependency_overrides` se mock karte hain. Part H mein poora dekhein.

## G.14 Production checklist (deploy se pehle)
| ✔ | Kya |
|---|---|
| ☐ | `uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4` (production mein `--reload` **nahi**) |
| ☐ | Docker image, ya Render/Railway/Fly.io/VPS par deploy. HTTPS (reverse proxy: Nginx/Caddy ya platform ka khud) |
| ☐ | Secrets env vars mein, `.env` git mein nahi |
| ☐ | Har external call par **timeout** + retry |
| ☐ | Ek jaisa error format, koi stack trace bahar nahi |
| ☐ | Logging: request ID, latency, status. Secrets aur personal data mask |
| ☐ | `GET /health` endpoint (load balancer/monitoring ke liye) |
| ☐ | Rate limiting (jaise `slowapi`), khaas kar LLM wale endpoints par (paise bachao!) |
| ☐ | Input limits: `max_length` taake koi 1 lakh lafz ka prompt na bheje |
| ☐ | CORS sirf apne domains ke liye, `*` nahi |
| ☐ | Tests CI mein (GitHub Actions) |
