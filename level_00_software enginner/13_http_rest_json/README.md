# M0.2 — The Web: HTTP, REST & JSON

CampusX AI Engineering Roadmap → Level 0 → Module 2

**Module ka goal:** Kisi bhi unfamiliar API ke docs parh ke khud request banana, response samajhna, aur ek sensible REST API design karna.

---

## 📁 Folder mein kya hai

| File | Kya hai |
|---|---|
| `README.md` | Saare concepts ke notes (yehi file) |
| `api_design.md` | REST design practice — apni watch store ke endpoints |
| `01_basic_requests.py` | Request/response cycle, methods, status codes, params |
| `02_json_pydantic.py` | JSON parse/produce + Pydantic se validation |
| `03_auth_headers.py` | `.env` se key, Bearer token, auth errors |
| `.env.example` | Template — copy karke `.env` banayein |
| `.gitignore` | `.env` aur `.venv` ko Git se bahar rakhta hai |
| `requirements.txt` | Packages: httpx, pydantic, python-dotenv |

---

## ⚙️ Setup (Windows PowerShell)

```powershell
cd m0.2-http-rest-json
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

Agar `Activate.ps1` pe "running scripts is disabled" error aaye to ek dafa ye chalayein:
```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Scripts chalane ke liye:
```powershell
python 01_basic_requests.py
python 02_json_pydantic.py
python 03_auth_headers.py
```

> uv use karte hain to: `uv venv`, `uv pip install -r requirements.txt`, `uv run 01_basic_requests.py`

Practice ke liye 2 free test APIs use hui hain — inhein koi key nahi chahiye:
- **jsonplaceholder.typicode.com** → fake posts/users (REST practice)
- **httpbin.org** → jo bhejo wapis dikhata hai, aur koi bhi status code de deta hai (debugging practice)

---

## 1. HTTP Request/Response Cycle

Client (aap) **request** bhejta hai → server process karta hai → **response** wapis aata hai.

**Request ke 4 hisse:**
- **URL** — kahan jaana hai
- **Method** — kya karna hai (GET, POST…)
- **Headers** — extra info (API key, content type)
- **Body** — asal data (aam tor pe JSON)

**Response ke 3 hisse:**
- **Status code** — kaam hua ya nahi
- **Headers**
- **Body** — asal jawab

> AI connection: `client.messages.create(...)` ke andar yahi cycle chalta hai. SDK sirf chhupa deta hai.

---

## 2. Methods & Idempotency

| Method | Kaam | Idempotent? |
|---|---|---|
| GET | Data lena | ✅ Haan |
| POST | Naya banana / action | ❌ Nahi |
| PUT | Poori cheez replace | ✅ Haan |
| PATCH | Thora hissa update | ⚠️ Aam tor pe nahi |
| DELETE | Mitana | ✅ Haan |

**Idempotent** = 1 baar bhejo ya 10 baar, result same.

**Kyun zaroori:** Retry logic. GET dobara bhejna safe hai. POST dobara bheja to 2 order ban jayenge / 2 WhatsApp messages chale jayenge. Isi liye Stripe jaisi APIs "idempotency key" header leti hain.

---

## 3. Status Codes

- **2xx** → sab theek
- **4xx** → **aapki** galti → request theek karo, retry bekaar
- **5xx** → **server** ki galti → thori der baad retry kar sakte ho

| Code | Matlab | AI scenario |
|---|---|---|
| 200 | OK | LLM ne jawab de diya |
| 201 | Created | Naya record ban gaya |
| 400 | Bad Request | JSON body galat |
| 401 | Unauthorized | API key galat / missing |
| 403 | Forbidden | Key theek, permission nahi |
| 404 | Not Found | Galat URL / cheez exist nahi karti |
| 409 | Conflict | Same cheez pehle se hai |
| 422 | Unprocessable | Format theek, data invalid (FastAPI mein bohot aata hai) |
| 429 | Too Many Requests | **Rate limit** — wait karke retry (exponential backoff) |
| 500 | Server Error | Unki taraf kuch toota |

> Sab se zyada `401` aur `429` dekhne ko milenge.

---

## 4. Headers, Params, Body & Cookies

```
GET https://mystore.com/api/products/123/reviews?limit=5&sort=new
                                     ^^^          ^^^^^^^^^^^^^^^
                                 path param       query params
```

- **Path param** → *kaunsi* cheez (`/products/123`)
- **Query params** → filter/options (`?limit=5`)
- **Headers** → URL mein nazar nahi aate (`Authorization`, `Content-Type`)
- **Body** → POST/PUT/PATCH ka data
- **Content-Type** → body ka format batata hai; `application/json` sab se common
- **Cookies** → zyada tar browser login sessions; APIs mein tokens zyada chalte hain

Python (httpx) mein:
```python
httpx.get(url, params={...}, headers={...})
httpx.post(url, json={...}, headers={...})   # json= khud Content-Type set kar deta hai
```

---

## 5. JSON

```json
{"name": "Casio Edifice", "price": 18500, "in_stock": true, "tags": ["analog", "men"]}
```

| JSON | Python |
|---|---|
| object `{}` | dict |
| array `[]` | list |
| `true` / `false` | `True` / `False` |
| `null` | `None` |

- `json.loads(text)` → text se dict (**parse**)
- `json.dumps(obj)` → dict se text (**produce**)
- `response.json()` → response body seedha dict mein

**AI ke liye sab se important:** LLM se structured JSON mangwaya jaata hai, aur wo kabhi kabhi toota hua deta hai (extra text, missing bracket, galat field). Isliye **hamesha validate karo** — Pydantic se.

---

## 6. RESTful Resource Design

**URL = noun (cheez), Method = verb (kaam).**

❌ Galat:
```
/getAllOrders   /createOrder   /deleteOrderById?id=5
```

✅ REST:
```
GET    /orders             saare orders
GET    /orders/5           order #5
POST   /orders             naya order
PATCH  /orders/5           order #5 update
DELETE /orders/5           order #5 delete
GET    /customers/7/orders customer 7 ke orders
```

Rules:
- Plural nouns (`/orders`, not `/order`)
- Lowercase, hyphens (`/order-items`)
- Nesting sirf ek-do level tak
- Filtering/sorting/pagination query params se (`?status=pending&page=2`)
- Sahi status code wapis karo (create pe 201, not found pe 404)

👉 Practice: `api_design.md`

---

## 7. Authentication Basics

- **API key** → secret string; kabhi custom header mein (`x-api-key`)
- **Bearer token** → `Authorization: Bearer <token>` (OpenAI aur bohot si APIs)
- **Authorization header** → wo header jismein credentials jaate hain

**3 sakht rules:**
1. Key **URL mein nahi** (`?api_key=...`) → URLs logs aur history mein save hote hain
2. Key **frontend / browser code mein nahi** → koi bhi parh sakta hai; hamesha backend pe
3. Key **code mein hardcode nahi** → `.env` mein rakho, `.env` ko `.gitignore` mein daalo

```python
import os
from dotenv import load_dotenv
load_dotenv()
key = os.getenv("MY_API_KEY")
```

---

## 8. curl & Postman / Bruno

**Windows PowerShell mein `curl` asal mein `Invoke-WebRequest` hota hai.** Asli curl ke liye `curl.exe` likhein:

```powershell
# GET, -i se status + headers bhi dikhte hain
curl.exe -i https://jsonplaceholder.typicode.com/posts/1

# Query param
curl.exe "https://jsonplaceholder.typicode.com/posts?userId=1"

# POST with JSON body (PowerShell mein quotes ka dhyan)
curl.exe -i -X POST https://jsonplaceholder.typicode.com/posts -H "Content-Type: application/json" -d '{\"title\":\"Casio\",\"userId\":1}'

# Bearer token
curl.exe -i https://httpbin.org/bearer -H "Authorization: Bearer test123"

# Koi bhi status code dekhna
curl.exe -i https://httpbin.org/status/429
```

**Postman / Bruno:** GUI tools — URL, method, headers, body form mein bharo, Send dabao. Bruno free aur lightweight hai (usebruno.com).

---

## ✅ Module complete kab samjhein

- [ ] Saari 3 `.py` files chala li aur unke TODO exercises kar liye
- [ ] `api_design.md` mein apne endpoints likh liye
- [ ] `curl.exe` se upar wali 5 commands chala ke output samjha
- [ ] **Final test:** Kisi asli API ke docs kholo (Anthropic / OpenAI / WhatsApp Cloud API) aur bina code chalaye bata sako — kaunsa method, URL, headers, body chahiye, aur kaunse error codes aa sakte hain

Sources: [CampusX Roadmap — Level 0](https://ai-engineer-roadmap-2026.vercel.app/level/0/)
