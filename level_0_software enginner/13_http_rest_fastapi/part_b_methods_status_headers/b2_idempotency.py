"""
B.2 Idempotency-Key: duplicate orders se bachao
===============================================
    python -m part_b_methods_status_headers.b2_idempotency

Theory: part_b_methods_status_headers/NOTES.md (B.2)
"""
import uuid

from common import USER, get_client

client = get_client()
body = {"product_id": 2, "qty": 1, "customer_phone": "923001234567"}

print("[X] Bina Idempotency-Key, 2 baar bheja (jaise network fail ke baad retry):")
for _ in range(2):
    print("   order id:", client.post("/orders", json=body, headers=USER).json()["id"])
print("   -> 2 alag orders ban gaye! Customer ko 2 watches mil jayen gi.")

print("\n[OK] Same Idempotency-Key ke saath, 2 baar bheja:")
key = str(uuid.uuid4())
for _ in range(2):
    r = client.post("/orders", json=body, headers={**USER, "Idempotency-Key": key})
    print("   status:", r.status_code, "| order id:", r.json()["id"])
print("   -> Pehli baar 201 (bana), doosri baar 200 (wahi purana order wapas).")

print("\n[!] Same key, lekin body alag:")
r = client.post("/orders", json={**body, "qty": 5}, headers={**USER, "Idempotency-Key": key})
print("  ", r.status_code, r.json())

client.close()
