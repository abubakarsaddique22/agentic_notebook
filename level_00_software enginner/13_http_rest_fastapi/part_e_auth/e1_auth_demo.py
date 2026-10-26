"""
E.1 401 vs 403 + secrets ko mask karna
======================================
    python -m part_e_auth.e1_auth_demo

Theory: part_e_auth/NOTES.md
"""
from common import USER, get_client

client = get_client()

# Ek order banao taake neeche ke checks ke liye ID ho
oid = client.post("/orders", json={"product_id": 1, "qty": 1, "customer_phone": "923001234567"}, headers=USER).json()["id"]

r = client.get(f"/orders/{oid}")
print("Bina key   :", r.status_code, "| WWW-Authenticate:", r.headers.get("www-authenticate"))
print("Ghalat key :", client.get(f"/orders/{oid}", headers={"Authorization": "Bearer chori-ki-key"}).status_code)
print("Sahi key   :", client.get(f"/orders/{oid}", headers=USER).status_code)
print("User delete:", client.delete(f"/orders/{oid}", headers=USER).status_code, "(pehchaan hai, ijazat nahi = 403)")


def mask(secret: str, keep: int = 4) -> str:
    """Logs mein secret ka sirf shuru ka hissa dikhao."""
    return secret[:keep] + "*" * 4 if secret else ""


print("Log mein   :", mask("sk-proj-abc123xyz789"))
client.close()
