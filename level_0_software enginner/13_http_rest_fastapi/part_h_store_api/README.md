# PART H: 🏗️ Mini Project: Store Support API (production style)

Sab kuch ek jagah: **routers, schemas, dependencies, settings, services, middleware, error handlers, lifespan, tests**.

```
part_h_store_api/
├── .env                    ← secrets (git mein NAHI)
├── .env.example            ← template (git mein jata hai)
├── pyproject.toml          ← pytest settings
├── try_api.py              ← chalte server ko requests bhejo
├── app/
│   ├── main.py             ← create_app(): middleware, errors, routers jorna
│   ├── config.py           ← Settings (pydantic-settings)
│   ├── schemas.py          ← Pydantic In/Out models
│   ├── deps.py             ← Depends: auth, llm
│   ├── services/
│   │   ├── llm.py          ← LLM client (yahan fake, 0.5s)
│   │   └── orders.py       ← data layer (yahan dict, asal mein DB/Shopify)
│   └── routers/
│       ├── health.py
│       ├── orders.py
│       └── chat.py
└── tests/
    ├── conftest.py         ← TestClient + fake LLM override
    ├── test_health.py
    ├── test_orders.py
    └── test_chat.py
```

**Layers ka usool:** `routers` (HTTP) → `services` (business logic) → data. Router mein SQL ya LLM ka detail nahi hota, aur service ko HTTP ka pata nahi hota. Is se testing aur badalna aasan hai.

## Chalana (Windows cmd, is folder ke andar)

```
cd part_h_store_api
```

**1. Tests:**
```
python -m pytest -v
```
Saare tests 1 second se kam mein, kyun ke LLM mock hai (`conftest.py` ka `InstantLLM`).

**2. Asli server:**
```
uvicorn app.main:app --reload --port 8767
```
Browser: http://127.0.0.1:8767/docs → "Authorize" ki jagah har endpoint mein `x-api-key` field mein `dev-key-2` daalein.

**3. Doosri cmd window se requests:**
```
python try_api.py
```

## Khud aage barhayein
1. `POST /v1/orders/{order_id}/cancel` banayein: `delivered` order par 409
2. Iska test `tests/test_orders.py` mein likhein
3. `FakeLLM` ki jagah asli `AsyncOpenAI`/`AsyncAnthropic` client lagayein (key `.env` se)
4. Part G.11 wala WhatsApp webhook `app/routers/webhooks.py` mein le aayein
