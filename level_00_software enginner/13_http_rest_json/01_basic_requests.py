"""
01 — Basic Requests
Concepts: request/response cycle, methods, status codes, path & query params, headers

Chalayein:  python 01_basic_requests.py
Test API:   https://jsonplaceholder.typicode.com  (fake data, koi key nahi)
            https://httpbin.org                   (debugging helper)
"""

import httpx

BASE = "https://jsonplaceholder.typicode.com"


def section(title: str) -> None:
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


# ------------------------------------------------------------
# 1. GET — data lena (request/response cycle dekho)
# ------------------------------------------------------------
section("1. GET /posts/1  →  ek post lao")

r = httpx.get(f"{BASE}/posts/1")

print("Request :", r.request.method, r.request.url)
print("Status  :", r.status_code, r.reason_phrase)
print("Content-Type header:", r.headers.get("content-type"))
print("Body (dict):", r.json())


# ------------------------------------------------------------
# 2. Path param vs Query param
# ------------------------------------------------------------
section("2. Path param vs Query param")

user_id = 1
# Path param → kaunsi cheez:   /users/1
r = httpx.get(f"{BASE}/users/{user_id}")
print("Path param  → user name:", r.json()["name"])

# Query param → filter:       /posts?userId=1
r = httpx.get(f"{BASE}/posts", params={"userId": user_id})
print("Query param → final URL:", r.request.url)
print("Is user ke posts:", len(r.json()))


# ------------------------------------------------------------
# 3. POST — naya cheez banana (201 Created)
# ------------------------------------------------------------
section("3. POST /posts  →  naya post banao")

new_post = {"title": "Casio Edifice review", "body": "Bohot achhi watch", "userId": 1}
r = httpx.post(f"{BASE}/posts", json=new_post)  # json= → Content-Type khud set

print("Status :", r.status_code)  # 201 hona chahiye
print("Request Content-Type:", r.request.headers.get("content-type"))
print("Server ne wapis bheja:", r.json())


# ------------------------------------------------------------
# 4. PATCH & DELETE
# ------------------------------------------------------------
section("4. PATCH (thora update) aur DELETE")

r = httpx.patch(f"{BASE}/posts/1", json={"title": "Updated title"})
print("PATCH status:", r.status_code, "| naya title:", r.json()["title"])

r = httpx.delete(f"{BASE}/posts/1")
print("DELETE status:", r.status_code)

# Note: jsonplaceholder fake hai, asal mein kuch save/delete nahi hota.


# ------------------------------------------------------------
# 5. Status codes handle karna
# ------------------------------------------------------------
section("5. Status codes — 2xx / 4xx / 5xx")


def explain(code: int) -> str:
    if 200 <= code < 300:
        return "✅ Success"
    if code == 401:
        return "🔑 Key galat/missing — request theek karo"
    if code == 404:
        return "❓ Cheez nahi mili — URL/id check karo"
    if code == 429:
        return "⏳ Rate limit — wait karke retry karo"
    if 400 <= code < 500:
        return "❌ Client ki galti — retry bekaar, request theek karo"
    if code >= 500:
        return "🔥 Server ki galti — thori der baad retry"
    return "?"


for code in [200, 404, 401, 429, 500]:
    try:
        r = httpx.get(f"https://httpbin.org/status/{code}", timeout=15)
        print(f"{r.status_code}  →  {explain(r.status_code)}")
    except httpx.HTTPError as e:
        print(f"{code}  →  network error: {e}")

# raise_for_status(): 4xx/5xx pe exception phenk deta hai
r = httpx.get(f"{BASE}/posts/99999")
try:
    r.raise_for_status()
except httpx.HTTPStatusError as e:
    print("\nraise_for_status() ne pakra:", e.response.status_code)


# ------------------------------------------------------------
# 6. Apni bheji hui request dekhna (httpbin echo)
# ------------------------------------------------------------
section("6. httpbin — server ko asal mein kya pohncha?")

r = httpx.post(
    "https://httpbin.org/post",
    params={"source": "practice"},
    headers={"X-Custom-Header": "abubakar-test"},
    json={"watch": "Seiko 5"},
    timeout=15,
)
echo = r.json()
print("Query args :", echo["args"])
print("Custom hdr :", echo["headers"].get("X-Custom-Header"))
print("JSON body  :", echo["json"])


# ============================================================
# 🏋️ TODO EXERCISES — khud karein
# ============================================================
# 1. GET /comments?postId=3 se comments lao aur har comment ka sirf "email" print karo.
# 2. GET /users/11 bhejo. Status code kya aaya? Kyun? (hint: kitne users hain?)
# 3. PUT /posts/1 bhejo poore naye data ke saath. PUT aur PATCH ke response mein farq dekho.
# 4. Ek function likho get_post(post_id) jo 404 pe None return kare, 200 pe dict.
# 5. httpbin.org/status/429 ko 3 dafa retry karo, har dafa wait double (1s, 2s, 4s).
#    (Ye "exponential backoff" hai — LLM APIs ke saath bohot kaam aata hai.)
