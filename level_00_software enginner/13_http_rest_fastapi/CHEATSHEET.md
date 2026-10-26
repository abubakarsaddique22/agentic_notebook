# PART K: 📌 Cheat Sheet

### HTTP
```
Request  = METHOD + URL + headers + body
Response = STATUS + headers + body
2xx ✅ success | 3xx ↪ redirect | 4xx ❌ client ki ghalti | 5xx 💥 server ki ghalti
Retry sirf: 429, 500, 502, 503, 504, timeouts (backoff + jitter + Retry-After)
401 = kaun ho? | 403 = ijazat nahi | 404 = nahi mila | 409 = takraav | 422 = validation
Path = kaunsi cheez | Query = filter/page | Body = data | Header = meta/auth
```

### httpx
```python
with httpx.Client(base_url=URL, timeout=10, headers={"Authorization": f"Bearer {key}"}) as c:
    r = c.get("/items", params={"limit": 10})
    r.raise_for_status()
    data = r.json()

async with httpx.AsyncClient(base_url=URL) as ac:
    results = await asyncio.gather(*(ac.get(f"/items/{i}") for i in ids))

with c.stream("GET", "/stream") as r:
    for line in r.iter_lines(): ...
```

### FastAPI
```python
app = FastAPI(lifespan=lifespan)

@app.get("/items/{item_id}", response_model=ItemOut)
async def read(item_id: Annotated[int, Path(gt=0)],
               q: Annotated[str | None, Query(max_length=50)] = None,
               user: Annotated[User, Depends(current_user)] = None): ...

@app.post("/items", status_code=201)
def create(item: ItemIn): ...

raise HTTPException(404, "nahi mila")
app.include_router(router, prefix="/v1")
app.dependency_overrides[get_llm] = lambda: FakeLLM()      # tests
```
```
uvicorn app.main:app --reload                      # development
uvicorn app.main:app --host 0.0.0.0 --workers 4    # production
```

### Sync vs Async
| Andar kya hai | Endpoint |
|---|---|
| `await` wali library (httpx.AsyncClient, async LLM SDK) | `async def` |
| Blocking library (requests, sync SDK, time.sleep) | `def` |
| CPU heavy (inference) | `def` / worker / alag service |

### Apne WhatsApp bot mein kya lagana hai
1. `POST /v1/webhooks/whatsapp`: signature check, `message_id` dedupe, jaldi 200, kaam background/queue mein
2. Shopify aur LLM ko **shared `httpx.AsyncClient`** se, timeout + retry ke saath
3. `pydantic-settings` + `.env` (`SecretStr`), aur `.env` git mein nahi
4. Ek jaisa error format, request ID middleware, logging
5. pytest + `TestClient` + LLM/Shopify mock

**Agla qadam:** `part_h_store_api` ko apne WhatsApp bot ka base bana lein, aur `FakeLLM` ki jagah asli `AsyncOpenAI`/`AsyncAnthropic` client lagayein. 🚀
