# PART F: Python HTTP Client (`httpx`)

> Saari files ke liye practice server chalna chahiye (`f7_public_api.py` ke ilawa).

AI engineer ka **aadha kaam client hona** hai: LLM APIs, vector DBs, Shopify, WhatsApp, sab ko HTTP requests.

| | `requests` | `httpx` |
|---|---|---|
| Sync | ✅ | ✅ (same API) |
| **Async** | ❌ | ✅ `httpx.AsyncClient` |
| HTTP/2 | ❌ | ✅ |
| Default timeout | ❌ **koi nahi (hamesha intezar!)** | ✅ 5 sec |
| FastAPI TestClient | | iske upar bana hai |
| OpenAI/Anthropic SDKs | | andar `httpx` use karte hain |

**Naye code mein `httpx` use karein.** `requests` purane code mein milta rahe ga, aur syntax 90% same hai.

## F.1 Client reuse karein
`httpx.get(...)` har baar **naya connection** banata hai. `httpx.Client()` connection **reuse** karta hai (keep-alive), jo bohat tez hai. `base_url`, headers aur timeout bhi ek jagah set ho jaate hain.

▶ `python -m part_f_httpx_client.f1_client_reuse`

## F.2 ⏱️ Timeouts: hamesha lagayein
Bina timeout ke, agar server phans jaye to aap ka program **hamesha ke liye** ruk jaata hai, aur WhatsApp bot jawab dena band kar deta hai. `httpx.Timeout(connect=5, read=60, ...)` se alag alag hisson ka timeout.

▶ `python -m part_f_httpx_client.f2_timeouts`

## F.3 Error handling: 3 kism ki ghaltiyan

| Kism | Exception | Matlab |
|---|---|---|
| Network | `httpx.ConnectError` | Server tak pohanche hi nahi (down, ghalat URL, internet) |
| Time | `httpx.TimeoutException` | Pohanche lekin jawab late |
| HTTP | `httpx.HTTPStatusError` (sirf `raise_for_status()` ke baad) | Jawab aaya lekin 4xx/5xx |

⚠️ `httpx` 404/500 par **khud error nahi deta**, `r.status_code` check karna ya `r.raise_for_status()` chalana parta hai.

▶ `python -m part_f_httpx_client.f3_error_handling`

## F.4 🔁 Retry + Exponential Backoff (LLM APIs ke liye zaroori)

`429` ya `5xx` aaye to **foran dobara** bhejna masla barhata hai. Is ki jagah:
- **Exponential backoff:** 1s → 2s → 4s → 8s intezar
- **Jitter:** thora random waqt jorein, taake 1000 clients ek hi second par wapas na aayein
- **`Retry-After` header** ho to us ki baat maanein
- **Max retries** rakhein, hamesha nahi
- Sirf **idempotent** requests, ya Idempotency-Key ke saath retry karein

> Real projects mein `tenacity` library ya SDK ki built-in retry (OpenAI/Anthropic SDK mein `max_retries`) use hoti hai. Lekin interview mein aksar ye **khud likhwate** hain.

▶ `python -m part_f_httpx_client.f4_retry_backoff`

## F.5 ⚡ Async: kai requests ek saath (concurrency)

5 LLM calls, har ek 1 second. **Ek ke baad ek = 5 second. Ek saath = 1 second.**
RAG mein kai documents embed karna, ya kai chunks summarize karna, isi tareeqe se tez hota hai.

- `.py` script mein async code `asyncio.run(main())` se chalta hai (notebook mein seedha `await` likh dete the)
- 1000 requests ek saath bhejein ge to rate limit (429) lag jaye ga. `asyncio.Semaphore(N)` se ek waqt mein sirf N requests

▶ `python -m part_f_httpx_client.f5_async_concurrency`

## F.6 🌊 Streaming responses (ChatGPT jaisa token by token)

LLM jawab **tukron mein** bhejta hai taake user ko intezar na karna pare. Format aam taur par **Server-Sent Events (SSE)** hota hai: har tukra `data: ...` line, aur beech mein khali line.

▶ `python -m part_f_httpx_client.f6_streaming`

## F.7 curl, Postman/Bruno aur browser DevTools

Code likhne se pehle API ko **haath se** test karna. API docs mein misalein aksar `curl` mein hoti hain.

**Windows PowerShell mein `curl` ki jagah `curl.exe` likhein**, kyun ke PowerShell mein `curl` ek doosri command (`Invoke-WebRequest`) ka naam hai. CMD mein `curl` theek chalta hai.

Server chalte hue, doosri window mein try karein:
```
curl.exe http://127.0.0.1:8765/products/1
curl.exe -i http://127.0.0.1:8765/products/1
curl.exe "http://127.0.0.1:8765/products?category=watches"
curl.exe -X POST http://127.0.0.1:8765/orders -H "Authorization: Bearer practice-key-123" -H "Content-Type: application/json" -d "{\"product_id\": 1, \"qty\": 1, \"customer_phone\": \"923001234567\"}"
```

| Flag | Matlab |
|---|---|
| `-i` | Response headers dikhao |
| `-v` | Sab kuch (request bhi), debugging ke liye |
| `-X POST` | Method |
| `-H "K: V"` | Header |
| `-d "..."` | Body |

**Tips:**
- **Browser DevTools** (`F12` → Network tab) → kisi request par right click → **Copy as cURL**. Kisi bhi website ki request dobara chala sakte hain
- **Postman / Bruno** mein curl **import** ho jata hai. Bruno free hai aur collections ko files mein save karta hai (git mein rakh sakte hain)
- FastAPI ka **`/docs`** page browser mein khud Postman jaisa kaam karta hai: http://127.0.0.1:8765/docs

▶ (internet chahiye) `python -m part_f_httpx_client.f7_public_api`
