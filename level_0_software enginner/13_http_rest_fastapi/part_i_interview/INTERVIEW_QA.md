# PART I: 🎤 Interview Q&A (chhote, pakke jawab)

> Practice ka tareeqa: sawal parhein, jawab chhupa kar **bol kar** jawab dein, phir milayein.

## HTTP / Web
1. **HTTP stateless ka matlab?** Server har request ko akela dekhta hai. State (login) ke liye har request mein token/cookie bhejni parti hai.
2. **HTTP vs HTTPS?** HTTPS = HTTP + TLS encryption. Data beech mein koi parh/badal nahi sakta, aur certificate server ki pehchaan saabit karta hai.
3. **GET vs POST?** GET data parhta hai, safe aur idempotent hai, cache ho sakta hai, aur body nahi hoti. POST naya banata/action karta hai, idempotent nahi, data body mein.
4. **PUT vs PATCH?** PUT poora resource replace karta hai (idempotent). PATCH sirf diye gaye fields badalta hai.
5. **Idempotency kya hai, kyun zaroori?** Ek request kai baar = ek baar jaisa asar. Retries (network fail, webhook retry) mein duplicates/double payment se bachata hai. POST ke liye Idempotency-Key.
6. **401 vs 403?** 401: authentication nahi/ghalat ("kaun ho?"). 403: pehchaan hai lekin ijazat nahi.
7. **400 vs 422?** 400: request bigri hui/samajh nahi aayi. 422: format theek, lekin values validation fail (FastAPI default).
8. **429 aaye to kya karein?** `Retry-After` ka intezar, exponential backoff + jitter, concurrency kam, request batching/caching.
9. **502 vs 503 vs 504?** 502: gateway ko upstream se ghalat jawab mila. 503: server khud busy/down. 504: upstream ne waqt par jawab nahi diya.
10. **CORS kya hai?** Browser ki security jo doosre domain ki API ka jawab tab tak JS ko nahi deti jab tak server `Access-Control-Allow-Origin` se ijazat na de. Sirf browsers par lagu.
11. **Cookie vs token?** Cookie browser khud save aur bhejta hai (sessions). Token client `Authorization` header mein lagata hai (APIs/mobile).
12. **API key URL mein kyun nahi?** URLs logs, history, proxies aur referer headers mein save ho jaate hain.

## REST / JSON
13. **REST ke principles?** Resources + nouns, HTTP methods se kaam, stateless, sahi status codes, ek jaisa representation (JSON), versioning.
14. **Pagination ke tareeqe?** Offset/limit (aasan, bari tables par slow) aur cursor (tez/stable, Shopify/Stripe).
15. **API versioning kaise?** URL `/v1/` (sab se common), ya header. Breaking change par naya version, purana kuch der chalta rahe.
16. **LLM ke JSON output ko reliable kaise banayein?** Structured outputs/tool calling, Pydantic validation, fence/extra text strip, fail par retry (error message ke saath) ya fallback.

## FastAPI
17. **FastAPI kyun?** Type hints se validation, auto docs, native async, DI, tez, aur AI ecosystem ka standard.
18. **WSGI vs ASGI?** WSGI sirf sync. ASGI async, WebSockets aur streaming support karta hai. FastAPI ASGI (uvicorn).
19. **`def` vs `async def` endpoint?** `def` thread pool mein chalta hai. `async def` event loop par. `async def` mein blocking call poora server rok deti hai.
20. **CPU heavy kaam (model inference) kaise handle?** `def` endpoint, `run_in_threadpool`/process pool, alag worker (Celery), ya alag model server. Async CPU kaam tez nahi karta.
21. **Dependency Injection ka fayda?** Auth/DB/settings ka code ek jagah, chains, aur tests mein `dependency_overrides` se fake.
22. **`response_model` kyun?** Output validate karta hai aur secret/extra fields filter karta hai, aur docs mein shape dikhata hai.
23. **Startup par model/client ek baar kaise load karein?** `lifespan` context manager, aur `app.state` mein rakhein.
24. **Background tasks vs task queue?** `BackgroundTasks` chhote kaam ke liye (response ke baad, usi process mein, restart par kho jaata hai). Bare/zaroori kaam ke liye Celery/RQ/Redis queue (retry, persistence).
25. **FastAPI app ko test kaise karte hain?** `TestClient` (bina server ke) + pytest, external services/LLM ko `dependency_overrides` ya `httpx.MockTransport` se mock.

## Bonus (Part A.3)
- **Browser mein URL likh kar Enter dabane par kya hota hai?** → `part_a_http_basics/NOTES.md` dekhein (DNS → TCP → TLS → HTTP → server → response → render → keep-alive)
- **`hmac.compare_digest` kyun?** → timing attack (Part G.11)
