# PART B: Methods, Status Codes, Headers, Params, Cookies

> Saari files ke liye practice server chalna chahiye:
> `uvicorn practice_server:app --port 8765 --reload`

## B.1 HTTP Methods

| Method | Kaam | Body? | **Safe?** | **Idempotent?** | Success code |
|---|---|---|---|---|---|
| `GET` | Data parhna | ❌ | ✅ | ✅ | 200 |
| `POST` | Naya banana / koi action | ✅ | ❌ | ❌ | 201 (naya bana) / 200 |
| `PUT` | **Poora** resource replace | ✅ | ❌ | ✅ | 200 |
| `PATCH` | **Thora** sa hissa badalna | ✅ | ❌ | ⚠️ aam taur par haan, guarantee nahi | 200 |
| `DELETE` | Mitana | ❌ | ❌ | ✅ | 204 (No Content) / 200 |
| `HEAD` | GET jaisa, lekin sirf headers | ❌ | ✅ | ✅ | 200 |
| `OPTIONS` | Kaunse methods allowed hain (CORS preflight) | ❌ | ✅ | ✅ | 204/200 |

- **Safe** = server par kuch **badalta nahi** (sirf parhna)
- **Idempotent** = ek hi request **1 baar ya 10 baar** bhejo, server ki **haalat (state) ek jaisi** rehti hai

> 🎤 **Interview:** "PUT vs PATCH?" PUT mein **poora** object bhejte hain aur jo field nahi bheja woh khatam/default ho jata hai. PATCH mein **sirf badalne wale** fields bhejte hain.

▶ `python -m part_b_methods_status_headers.b1_order_lifecycle` (POST → GET → PATCH → PUT → DELETE)

## B.2 Idempotency: real kaam mein kyun aham hai

**Masla:** Aap ne `POST /orders` bheja, network beech mein toot gaya, aur response nahi aaya. Order bana ya nahi? Agar dobara bhejo to **2 order** ban sakte hain (ya customer se **2 baar paise** kat sakte hain!).

**Hal: Idempotency-Key.** Client ek unique key (UUID) header mein bhejta hai. Server us key ko yaad rakhta hai, aur **dobara wahi key aaye to naya kaam nahi karta**, pehla jawab hi lauta deta hai. Stripe, PayPal aur bohat se payment APIs isi tareeqe se kaam karte hain.

**WhatsApp/webhook mein:** WhatsApp ek hi message ka webhook **dobara** bhej sakta hai (retry). Aap `message_id` save kar ke duplicate ignore karte hain (Part G.11 mein banayein ge).

▶ `python -m part_b_methods_status_headers.b2_idempotency`

## B.3 Status Codes

Pehla digit **family** batata hai. Pehle family dekhein, phir exact code.

| Code | Naam | Kab | Real misal |
|---|---|---|---|
| **2xx ✅** | **Success** | | |
| `200` | OK | Kaam ho gaya | GET order |
| `201` | Created | Naya resource bana (+ `Location` header) | POST order |
| `202` | Accepted | Le liya, **baad mein** process hoga | Bara AI job queue mein |
| `204` | No Content | Ho gaya, body nahi | DELETE |
| **3xx ↪️** | **Redirect / Cache** | | |
| `301` / `308` | Moved Permanently | URL hamesha ke liye badal gaya | http → https |
| `302` / `307` | Temporary Redirect | Abhi doosri jagah jao | Login page |
| `304` | Not Modified | Cache wala version theek hai | Browser cache |
| **4xx ❌** | **Client ki ghalti** (request theek karo) | | |
| `400` | Bad Request | Request ghalat/samajh nahi aayi | Product mojood nahi |
| `401` | Unauthorized | **"Tum kaun ho?"** Key nahi ya ghalat | API key missing |
| `403` | Forbidden | **"Pata hai kaun ho, ijazat nahi"** | User delete kare (admin only) |
| `404` | Not Found | Resource nahi mila | Order 9999 |
| `405` | Method Not Allowed | Is URL par ye method nahi | GET ki jagah DELETE |
| `409` | Conflict | Current state se takraav | Duplicate email, Idempotency-Key mismatch |
| `422` | Unprocessable Entity | JSON sahi lekin **validation fail** | **FastAPI ka default validation error** |
| `429` | Too Many Requests | Rate limit (+ `Retry-After` header) | **OpenAI/Anthropic aksar dete hain** |
| **5xx 💥** | **Server ki ghalti** (retry kar sakte ho) | | |
| `500` | Internal Server Error | Server ke code mein crash | Unhandled exception |
| `502` | Bad Gateway | Beech wale server ko **upstream** se ghalat jawab mila | Aap ki API → Shopify down |
| `503` | Service Unavailable | Server busy ya maintenance | Overloaded |
| `504` | Gateway Timeout | Upstream ne waqt par jawab nahi diya | LLM ne 60 sec lagaye |

**Retry ka rule:** `429` aur `5xx` (500, 502, 503, 504) par **retry** karein (backoff ke saath). Baqi `4xx` par retry **bekaar** hai, pehle apni request theek karein.

**FastAPI ka `422` response:** `loc` batata hai **kaunsa field** ghalat hai, aur `msg` batata hai **kyun**.

▶ `python -m part_b_methods_status_headers.b3_status_codes`

## B.4 Headers

Headers = request/response ke baare mein **extra info** (`Naam: value`). Naam **case-insensitive** hote hain.

| Header | Kis mein | Kaam |
|---|---|---|
| `Content-Type` | Dono | Body kis format mein hai: `application/json`, `text/html`, `multipart/form-data` |
| `Accept` | Request | Mujhe jawab kis format mein chahiye |
| `Authorization` | Request | `Bearer <token>`, yani pehchaan |
| `User-Agent` | Request | Client kaun hai (browser/python-httpx) |
| `X-Request-ID` | Dono | Har request ka unique ID, logs mein trace karne ke liye |
| `Idempotency-Key` | Request | Duplicate se bachao (B.2) |
| `Location` | Response | Naye resource ka URL (201 ke saath) |
| `Retry-After` | Response | Kitne second baad try karein (429/503) |
| `Cache-Control` | Response | Kitni der cache kar sakte hain |
| `Set-Cookie` | Response | Browser ko cookie save karne ko kehna |
| `Access-Control-Allow-Origin` | Response | **CORS:** kaunsi website browser se ye API call kar sakti hai |

`X-` se shuru hone wale aam taur par **custom** headers hote hain.

▶ `python -m part_b_methods_status_headers.b4_headers`

## B.5 Data bhejne ki 4 jagahein: Path, Query, Body, Headers

```
POST /customers/5/orders?notify=true
     └────┬─────┘ └────┬────┘└────┬────┘
      resource   path param   query param
Authorization: Bearer xyz             ← header
Content-Type: application/json

{"product_id": 1, "qty": 2}           ← body
```

| Jagah | Kya bhejein | Misal |
|---|---|---|
| **Path param** | Kisi **ek** resource ki pehchaan (zaroori) | `/orders/1042` |
| **Query param** | Filter, sort, search, pagination (optional) | `?category=watches&max_price=5000` |
| **Body** | Bara/structured data, POST/PUT/PATCH | `{"product_id": 1, "qty": 2}` |
| **Header** | Request ke baare mein meta info, auth | `Authorization` |

**URL encoding:** URL mein space, Urdu ya `&` jaise characters seedhe nahi ja sakte. `httpx` khud encode kar deta hai, is liye **khud string jor kar URL na banayein**, `params=` use karein.

### Body ke formats (`Content-Type`)
| `httpx` argument | Content-Type | Kab |
|---|---|---|
| `json={...}` | `application/json` | **APIs mein 95% yahi** |
| `data={...}` | `application/x-www-form-urlencoded` | HTML forms, OAuth token requests |
| `files={...}` | `multipart/form-data` | File upload (PDF ko RAG ke liye, audio ko Whisper ke liye) |
| `content=b"..."` | khud set karein | Raw bytes |

▶ `python -m part_b_methods_status_headers.b5_params_and_body`

## B.6 Cookies vs Tokens

| | Cookie | Token (Bearer) |
|---|---|---|
| Kahan rakha jata hai | **Browser** khud save aur bhejta hai | Client code khud header mein lagata hai |
| Kaise jaata hai | `Cookie:` header (automatic) | `Authorization: Bearer ...` |
| Kahan zyada | Websites (login session) | **APIs**, mobile apps, server-to-server |
| Khatra | CSRF (is liye `HttpOnly`, `Secure`, `SameSite` flags) | Token chori ho jaye (XSS, logs) |

`httpx.Client` browser ki tarah cookies **yaad rakhta** hai.

▶ `python -m part_b_methods_status_headers.b6_cookies`
