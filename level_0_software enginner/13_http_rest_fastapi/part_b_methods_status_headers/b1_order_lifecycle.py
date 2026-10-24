"""
B.1 HTTP Methods: ek order ki poori zindagi (POST -> GET -> PATCH -> PUT -> DELETE)
==================================================================================
    python -m part_b_methods_status_headers.b1_order_lifecycle

Theory: part_b_methods_status_headers/NOTES.md (B.1)
"""
from common import ADMIN, USER, get_client

client = get_client()

# 1. POST: naya order banao  -> 201 + Location header
r = client.post("/orders", json={"product_id": 1, "qty": 1, "customer_phone": "923001234567"}, headers=USER)
print("POST  ", r.status_code, r.json(), "| Location:", r.headers.get("location"))
order_id = r.json()["id"]

# 2. GET: order parho  -> 200
r = client.get(f"/orders/{order_id}", headers=USER)
print("GET   ", r.status_code, r.json())

# 3. PATCH: sirf status badlo (baqi fields wese hi)
r = client.patch(f"/orders/{order_id}", json={"status": "shipped"}, headers=USER)
print("PATCH ", r.status_code, r.json())

# 4. PUT: poora order replace (naya product, nayi qty)
r = client.put(f"/orders/{order_id}", json={"product_id": 3, "qty": 2, "customer_phone": "923001234567"}, headers=USER)
print("PUT   ", r.status_code, r.json())

# 5. DELETE: user key se -> 403 (ijazat nahi), admin key se -> 204 (body khali)
r = client.delete(f"/orders/{order_id}", headers=USER)
print("DELETE", r.status_code, r.json())
r = client.delete(f"/orders/{order_id}", headers=ADMIN)
print("DELETE", r.status_code, "(body khali:", repr(r.text), ")")

# 6. Ab GET -> 404
r = client.get(f"/orders/{order_id}", headers=USER)
print("GET   ", r.status_code, r.json())

client.close()

# ---- Khud try karein ----
# PUT mein customer_phone hata kar bhejein. Kya hota hai? (Hint: 422, kyun ke PUT poora object maangta hai)
