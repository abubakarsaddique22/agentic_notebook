"""
B.3 Status codes: har family ki misal + FastAPI ka 422 parhna
=============================================================
    python -m part_b_methods_status_headers.b3_status_codes

Theory: part_b_methods_status_headers/NOTES.md (B.3)
"""
from common import USER, get_client, title

client = get_client()
client.post("/reset-counters")

# Pehle ek order bana lo taake neeche wale checks ke liye ID ho
existing = client.post("/orders", json={"product_id": 1, "qty": 1, "customer_phone": "923001234567"}, headers=USER).json()["id"]

title("Har request ka status code")
checks = [
    ("Product mila",             lambda: client.get("/products/1")),
    ("Order bana",               lambda: client.post("/orders", json={"product_id": 3, "qty": 1, "customer_phone": "923001234567"}, headers=USER)),
    ("Ghalat product id",        lambda: client.post("/orders", json={"product_id": 99, "qty": 1, "customer_phone": "923001234567"}, headers=USER)),
    ("Key nahi bheji",           lambda: client.get(f"/orders/{existing}")),
    ("User ne delete kiya",      lambda: client.delete(f"/orders/{existing}", headers=USER)),
    ("Product nahi mila",        lambda: client.get("/products/999")),
    ("Ghalat method",            lambda: client.delete("/products/1")),
    ("Validation fail (qty=50)", lambda: client.post("/orders", json={"product_id": 1, "qty": 50, "customer_phone": "92"}, headers=USER)),
    ("Rate limit",               lambda: client.get("/rate-limited")),
    ("Server busy",              lambda: client.get("/flaky")),
]
for name, call in checks:
    r = call()
    print(f"{r.status_code} {r.reason_phrase:<22} <- {name}")

title("FastAPI ka 422 response parhna: loc = kaunsa field, msg = kyun")
r = client.post("/orders", json={"product_id": "abc", "qty": 50, "customer_phone": "92"}, headers=USER)
for err in r.json()["detail"]:
    print(f"field: {err['loc']} | msg: {err['msg']} | diya: {err.get('input')}")

client.close()
