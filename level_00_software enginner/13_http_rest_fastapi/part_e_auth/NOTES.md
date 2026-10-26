# PART E: Authentication Basics

| | **Authentication (AuthN)** | **Authorization (AuthZ)** |
|---|---|---|
| Sawal | **Tum kaun ho?** | **Tum kya kar sakte ho?** |
| Fail | `401 Unauthorized` | `403 Forbidden` |
| Misal | API key ghalat | User key se admin ka kaam |

## E.1 Tareeqe
| Tareeqa | Kaise | Kahan |
|---|---|---|
| **API Key** | `X-API-Key: abc` ya `Authorization: Bearer abc` | Server-to-server (OpenAI, Anthropic, Shopify Admin API) |
| **Bearer Token** | `Authorization: Bearer <token>` | Login ke baad milne wala token |
| **Basic Auth** | `Authorization: Basic base64(user:pass)` | Purane/internal systems. **Sirf HTTPS par** |
| **JWT** | Token jis mein data (user id, expiry) **signed** hota hai | Stateless login. Server bina DB check ke verify kar leta hai |
| **OAuth 2.0** | "Login with Google", ya kisi app ko apne account tak ijazat dena | Shopify app install, Google APIs |
| **Webhook signature** | Body ka HMAC hash header mein | WhatsApp, Stripe, Shopify webhooks (G.11) |

> 🎤 **JWT ka concept:** teen hisse `header.payload.signature`, base64 mein. Payload **encrypted nahi, sirf signed** hai, yani koi bhi parh sakta hai lekin badal nahi sakta. Is liye JWT mein password jaisi secret cheezein kabhi na rakhein.

## E.2 🔐 Secrets ke sunehre usool
1. **URL mein kabhi nahi:** `?api_key=sk-...` server logs, browser history aur proxies mein save ho jaata hai
2. **Client code mein kabhi nahi:** website ka JavaScript, mobile app, ya public GitHub. Koi bhi nikaal sakta hai. Frontend → **aap ka backend** → OpenAI
3. **`.env` file** mein rakhein, aur `.env` ko `.gitignore` mein daalein
4. **Logs mein mask:** `sk-ab****`
5. **Rotate:** key leak ho jaye to foran nayi banayein aur purani band karein
6. **Least privilege:** sirf utni ijazat jitni zaroori (read-only key agar sirf parhna hai)

▶ `python -m part_e_auth.e1_auth_demo` (server chalna chahiye)
