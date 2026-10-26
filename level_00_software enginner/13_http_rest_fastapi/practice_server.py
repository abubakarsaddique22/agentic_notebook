"""
PRACTICE STORE API (local server)
=================================
Parts A se F tak aap "client" ban kar is server ko requests bhejein ge.

Chalane ka tareeqa (pehli cmd window mein, is folder ke andar se):

    uvicorn practice_server:app --port 8765 --reload

Phir browser mein kholein:  http://127.0.0.1:8765/docs
Is window ko khula rehne dein. Lessons doosri cmd window mein chalayein.

Abhi ye code samajhne ki zaroorat nahi. Part G (FastAPI) parhne ke baad
wapas aa kar parhein, sab samajh aa jaye ga.

Note: data memory (dict) mein hai. Server restart = saare orders saaf.
"""
import asyncio
import itertools
from typing import Annotated, Literal

from fastapi import Cookie, FastAPI, Header, HTTPException, Query, Request, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

app = FastAPI(title="Practice Store API", version="1.0")

PRODUCTS = {
    1: {"id": 1, "name": "Classic Watch", "category": "watches", "price": 4500},
    2: {"id": 2, "name": "Sport Watch", "category": "watches", "price": 6500},
    3: {"id": 3, "name": "Leather Wallet", "category": "wallets", "price": 1800},
    4: {"id": 4, "name": "Slim Wallet", "category": "wallets", "price": 1200},
    5: {"id": 5, "name": "Steel Watch", "category": "watches", "price": 9000},
    6: {"id": 6, "name": "Kids Watch", "category": "watches", "price": 2500},
    7: {"id": 7, "name": "Card Holder", "category": "wallets", "price": 900},
}
ORDERS: dict[int, dict] = {}
IDEMPOTENCY: dict[str, tuple[dict, dict]] = {}
NEXT_ID = itertools.count(1001)
USER_KEY, ADMIN_KEY = "practice-key-123", "admin-key-999"
COUNTERS = {"flaky": 0, "rate": 0}


class OrderIn(BaseModel):
    product_id: int
    qty: int = Field(gt=0, le=10)
    customer_phone: str = Field(min_length=10)


class StatusIn(BaseModel):
    status: Literal["pending", "shipped", "delivered", "cancelled"]


def auth(authorization: str | None, admin: bool = False):
    if authorization not in (f"Bearer {USER_KEY}", f"Bearer {ADMIN_KEY}"):
        raise HTTPException(401, "Login/API key missing ya ghalat",
                            headers={"WWW-Authenticate": "Bearer"})
    if admin and authorization != f"Bearer {ADMIN_KEY}":
        raise HTTPException(403, "Ye kaam sirf admin kar sakta hai")


@app.api_route("/echo", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def echo(request: Request):
    """Jo bheja, wahi wapas dikhata hai (httpbin jaisa)."""
    body = await request.body()
    keep = ("user-agent", "accept", "content-type", "authorization", "x-request-id", "cookie")
    headers = {k: v for k, v in request.headers.items() if k in keep or k.startswith("x-")}
    if "authorization" in headers:
        headers["authorization"] = headers["authorization"][:12] + "****"
    return {"method": request.method, "path": request.url.path,
            "query": dict(request.query_params), "headers": headers,
            "body": body.decode(errors="replace") or None}


@app.get("/products")
def list_products(category: str | None = None, max_price: int | None = None,
                  limit: Annotated[int, Query(ge=1, le=50)] = 3,
                  offset: Annotated[int, Query(ge=0)] = 0):
    items = [p for p in PRODUCTS.values()
             if (category is None or p["category"] == category)
             and (max_price is None or p["price"] <= max_price)]
    return {"items": items[offset:offset + limit], "total": len(items),
            "limit": limit, "offset": offset}


@app.get("/products/{product_id}")
def get_product(product_id: int):
    if product_id not in PRODUCTS:
        raise HTTPException(404, f"Product {product_id} nahi mila")
    return PRODUCTS[product_id]


@app.post("/orders", status_code=201)
def create_order(order: OrderIn, response: Response,
                 authorization: Annotated[str | None, Header()] = None,
                 idempotency_key: Annotated[str | None, Header()] = None):
    auth(authorization)
    if order.product_id not in PRODUCTS:
        raise HTTPException(400, "Ye product mojood nahi")
    if idempotency_key and idempotency_key in IDEMPOTENCY:
        saved_body, saved_order = IDEMPOTENCY[idempotency_key]
        if saved_body != order.model_dump():
            raise HTTPException(409, "Ye Idempotency-Key kisi aur order ke liye use ho chuki")
        response.status_code = 200
        return saved_order
    oid = next(NEXT_ID)
    new = {"id": oid, **order.model_dump(), "status": "pending",
           "total": PRODUCTS[order.product_id]["price"] * order.qty}
    ORDERS[oid] = new
    if idempotency_key:
        IDEMPOTENCY[idempotency_key] = (order.model_dump(), new)
    response.headers["Location"] = f"/orders/{oid}"
    return new


@app.get("/orders/{order_id}")
def get_order(order_id: int, authorization: Annotated[str | None, Header()] = None):
    auth(authorization)
    if order_id not in ORDERS:
        raise HTTPException(404, f"Order {order_id} nahi mila")
    return ORDERS[order_id]


@app.put("/orders/{order_id}")
def replace_order(order_id: int, order: OrderIn,
                  authorization: Annotated[str | None, Header()] = None):
    auth(authorization)
    if order_id not in ORDERS:
        raise HTTPException(404, f"Order {order_id} nahi mila")
    ORDERS[order_id] = {"id": order_id, **order.model_dump(), "status": ORDERS[order_id]["status"],
                        "total": PRODUCTS[order.product_id]["price"] * order.qty}
    return ORDERS[order_id]


@app.patch("/orders/{order_id}")
def update_status(order_id: int, body: StatusIn,
                  authorization: Annotated[str | None, Header()] = None):
    auth(authorization)
    if order_id not in ORDERS:
        raise HTTPException(404, f"Order {order_id} nahi mila")
    ORDERS[order_id]["status"] = body.status
    return ORDERS[order_id]


@app.delete("/orders/{order_id}", status_code=204)
def delete_order(order_id: int, authorization: Annotated[str | None, Header()] = None):
    auth(authorization, admin=True)
    if order_id not in ORDERS:
        raise HTTPException(404, f"Order {order_id} nahi mila")
    del ORDERS[order_id]


@app.post("/login")
def login(response: Response, username: str = "abubakar"):
    response.set_cookie("session_id", f"sess-{username}", httponly=True)
    return {"message": f"Welcome {username}, cookie set ho gayi"}


@app.get("/me")
def me(session_id: Annotated[str | None, Cookie()] = None):
    if not session_id:
        raise HTTPException(401, "Pehle /login karein")
    return {"session": session_id}


@app.get("/flaky")
def flaky():
    """Pehli 2 calls 503 deti hai, teesri 200 (retry practice)."""
    COUNTERS["flaky"] += 1
    if COUNTERS["flaky"] % 3 != 0:
        raise HTTPException(503, "Server busy, baad mein try karein")
    return {"message": f"Kaam ho gaya (attempt {COUNTERS['flaky']})"}


@app.post("/reset-counters")
def reset_counters():
    COUNTERS.update(flaky=0, rate=0)
    return {"reset": True}


@app.get("/rate-limited")
def rate_limited():
    """Har doosri call 429 deti hai (LLM APIs jaisa)."""
    COUNTERS["rate"] += 1
    if COUNTERS["rate"] % 2 == 1:
        raise HTTPException(429, "Bohat zyada requests", headers={"Retry-After": "1"})
    return {"message": "OK"}


@app.get("/slow")
async def slow(seconds: float = 2):
    await asyncio.sleep(seconds)
    return {"waited": seconds}


@app.get("/stream")
async def stream(prompt: str = "Salam"):
    """LLM jaisa token-by-token jawab (Server-Sent Events)."""
    async def tokens():
        for word in f"Aap ne kaha {prompt}. Ye jawab LLM ki tarah tukron mein aa raha hai.".split():
            await asyncio.sleep(0.15)
            yield f"data: {word}\n\n"
        yield "data: [DONE]\n\n"
    return StreamingResponse(tokens(), media_type="text/event-stream")
