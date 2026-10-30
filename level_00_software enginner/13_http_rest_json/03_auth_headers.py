"""
03 — Auth & Headers
Concepts: .env se secrets, Bearer token, Authorization header, 401/403, key URL mein kyun nahi

Chalayein:  python 03_auth_headers.py
Pehle:      copy .env.example .env
"""

import os

import httpx
from dotenv import load_dotenv

load_dotenv()  # .env file ki values environment mein daal deta hai


def section(title: str) -> None:
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


# ------------------------------------------------------------
# 1. .env se secret parhna (KABHI hardcode nahi)
# ------------------------------------------------------------
section("1. .env se token parhna")

token = os.getenv("PRACTICE_TOKEN")
if not token:
    raise SystemExit("❌ PRACTICE_TOKEN nahi mila. Pehle: copy .env.example .env")

# Secret kabhi poora print mat karo — sirf shuru ke kuch characters
print("Token mila:", token[:4] + "****")


# ------------------------------------------------------------
# 2. Bina token ke → 401
# ------------------------------------------------------------
section("2. Bina Authorization header ke")

r = httpx.get("https://httpbin.org/bearer", timeout=15)
print("Status:", r.status_code, "→ 401 = 'tum kaun ho?'")


# ------------------------------------------------------------
# 3. Bearer token ke saath → 200
# ------------------------------------------------------------
section("3. Authorization: Bearer <token>")

headers = {"Authorization": f"Bearer {token}"}
r = httpx.get("https://httpbin.org/bearer", headers=headers, timeout=15)
print("Status:", r.status_code)
print("Server ne dekha:", r.json())


# ------------------------------------------------------------
# 4. Client object — headers ek dafa set, har request mein jaayein
# ------------------------------------------------------------
section("4. httpx.Client — base_url + default headers")

with httpx.Client(
    base_url="https://httpbin.org",
    headers={"Authorization": f"Bearer {token}", "User-Agent": "abubakar-practice/1.0"},
    timeout=15,
) as client:
    r = client.get("/headers")
    sent = r.json()["headers"]
    print("Authorization gaya?:", "Authorization" in sent)
    print("User-Agent        :", sent.get("User-Agent"))
# Real projects (bot, RAG) mein yahi pattern use hota hai — ek client, baar baar use.


# ------------------------------------------------------------
# 5. ❌ Key URL mein kyun nahi daalni
# ------------------------------------------------------------
section("5. Galat tareeqa: key URL mein")

r = httpx.get("https://httpbin.org/get", params={"api_key": token}, timeout=15)
print("Ye poora URL server logs, proxy logs, browser history mein save hota hai:")
print("  ", r.request.url)
print("Header mein bhejo to URL saaf rehta hai.")


# ------------------------------------------------------------
# 6. (Optional) Asli LLM API — raw HTTP, bina SDK ke
# ------------------------------------------------------------
section("6. (Optional) Anthropic API raw HTTP se")

api_key = os.getenv("ANTHROPIC_API_KEY")
if not api_key:
    print("ANTHROPIC_API_KEY .env mein nahi — skip. (Isay chalane se thore paise lagte hain.)")
else:
    r = httpx.post(
        "https://api.anthropic.com/v1/messages",            # URL
        headers={                                            # Headers
            "x-api-key": api_key,                            #   auth (custom header style)
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={                                               # JSON body
            "model": "claude-haiku-5-5",
            "max_tokens": 50,
            "messages": [{"role": "user", "content": "Say hi in Urdu, one line."}],
        },
        timeout=30,
    )
    print("Status:", r.status_code)
    if r.status_code == 200:
        print("Jawab:", r.json()["content"][0]["text"])
    else:
        # Error body bhi JSON hoti hai — hamesha parho, wahan asal wajah likhi hoti hai
        print("Error body:", r.json())


# ============================================================
# 🏋️ TODO EXERCISES
# ============================================================
# 1. .env mein PRACTICE_TOKEN khaali kar do aur script chalao — kya hota hai?
# 2. Header ka naam galat likho ("Authorisation") — httpbin.org/bearer kya status deta hai?
# 3. "Bearer " hata ke sirf token bhejo — kya hota hai?
# 4. Section 6 mein jaan boojh ke galat ANTHROPIC_API_KEY daalo. Status code aur
#    error body note karo. (401 hona chahiye.)
# 5. Socho: WhatsApp bot mein Meta ka access token kahan rakhoge? Frontend? Backend? .env?
