"""
02 — JSON + Pydantic
Concepts: JSON parse/produce, nested data, validation, LLM ka toota hua JSON handle karna

Chalayein:  python 02_json_pydantic.py
"""

import json

import httpx
from pydantic import BaseModel, Field, ValidationError


def section(title: str) -> None:
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


# ------------------------------------------------------------
# 1. json.loads / json.dumps
# ------------------------------------------------------------
section("1. Parse (loads) aur Produce (dumps)")

text = '{"name": "Casio Edifice", "price": 18500, "in_stock": true, "tags": ["analog", "men"], "discount": null}'

data = json.loads(text)  # text → dict
print("Type:", type(data))
print("in_stock (Python mein True):", data["in_stock"])
print("discount (Python mein None):", data["discount"])

data["price"] = 17999
back_to_text = json.dumps(data, indent=2)  # dict → text
print("Wapis JSON text:\n", back_to_text)


# ------------------------------------------------------------
# 2. Nested JSON se data nikalna (real API)
# ------------------------------------------------------------
section("2. Nested JSON — /users/1")

user = httpx.get("https://jsonplaceholder.typicode.com/users/1").json()

print("Name   :", user["name"])
print("City   :", user["address"]["city"])               # dict ke andar dict
print("Lat    :", user["address"]["geo"]["lat"])         # aur andar
print("Company:", user.get("company", {}).get("name"))   # .get() → KeyError se bachao
print("Missing key safe:", user.get("whatsapp", "N/A"))


# ------------------------------------------------------------
# 3. Pydantic — data ka "contract" banana
# ------------------------------------------------------------
section("3. Pydantic validation")


class Watch(BaseModel):
    name: str
    price: int = Field(gt=0)          # 0 se zyada hona chahiye
    in_stock: bool
    tags: list[str] = []


good = {"name": "Seiko 5", "price": 32000, "in_stock": True, "tags": ["automatic"]}
watch = Watch(**good)
print("✅ Valid:", watch)
print("   Dot se access:", watch.name, watch.price)
print("   Wapis dict:", watch.model_dump())

bad = {"name": "Fake Rolex", "price": -500, "in_stock": "maybe"}
try:
    Watch(**bad)
except ValidationError as e:
    print("\n❌ Invalid data pakra gaya:")
    for err in e.errors():
        print(f"   field={err['loc']}  problem={err['msg']}")


# ------------------------------------------------------------
# 4. AI scenario — LLM ka output validate karna
# ------------------------------------------------------------
section("4. LLM output validate karna (WhatsApp bot jaisa)")


class Intent(BaseModel):
    intent: str
    order_id: str | None = None
    confidence: float = Field(ge=0, le=1)


# Ye 4 "LLM outputs" hain — jaise asal mein aa sakte hain
llm_outputs = [
    '{"intent": "order_status", "order_id": "1042", "confidence": 0.93}',          # perfect
    'Sure! Here is the JSON: {"intent": "greeting", "confidence": 0.8}',           # extra text
    '{"intent": "order_status", "order_id": "1042", "confidence": 0.9',            # toota bracket
    '{"intent": "refund", "confidence": 1.7}',                                     # galat value
]


def parse_llm_json(raw: str) -> Intent | None:
    # Step 1: agar aage peeche extra text hai to sirf { ... } wala hissa nikalo
    start, end = raw.find("{"), raw.rfind("}")
    if start == -1:
        print("   ❌ JSON mila hi nahi")
        return None
    # closing } na mile to string ke end tak lo — parse step khud error batayega
    candidate = raw[start : end + 1] if end > start else raw[start:]

    # Step 2: parse
    try:
        obj = json.loads(candidate)
    except json.JSONDecodeError as e:
        print(f"   ❌ JSON toota hua: {e.msg}")
        return None

    # Step 3: validate
    try:
        return Intent(**obj)
    except ValidationError as e:
        print(f"   ❌ Shape galat: {e.errors()[0]['msg']}")
        return None


for i, raw in enumerate(llm_outputs, 1):
    print(f"\nOutput {i}: {raw}")
    result = parse_llm_json(raw)
    if result:
        print("   ✅", result)

# Real life: invalid hone pe LLM ko dobara bhejo ("valid JSON do") — max 2-3 retries.


# ============================================================
# 🏋️ TODO EXERCISES
# ============================================================
# 1. GET /users se saare users lao, aur ek list banao: [{"name": ..., "city": ...}, ...]
#    phir use json.dumps(indent=2) se ek file "users.json" mein save karo.
# 2. "users.json" ko wapis json.load() se parho aur sirf Gwenborough wale users print karo.
# 3. Ek Pydantic model "Order" banao: order_id (str), items (list[str]),
#    total (int, > 0), status ("pending" | "shipped" | "delivered").
#    hint: from typing import Literal
# 4. 3 sahi aur 3 galat Order dicts bana ke test karo.
# 5. Watch model ko /posts/1 ke response pe lagao — kya error aata hai? Kyun?
