"""
B.4 Headers bhejna aur server ko kya mila, dekhna
=================================================
    python -m part_b_methods_status_headers.b4_headers

/echo endpoint jo bheja wahi wapas dikhata hai.
Theory: part_b_methods_status_headers/NOTES.md (B.4)
"""
import json

from common import get_client

client = get_client()

r = client.get("/echo", headers={
    "Accept": "application/json",
    "User-Agent": "abubakar-bot/1.0",
    "X-Request-ID": "req-42",
    "Authorization": "Bearer practice-key-123",
})
print(json.dumps(r.json(), indent=2))
print("\nNote: server ne authorization ko '****' se mask kiya. Secrets kabhi poore log na karein.")

print("\nResponse ke headers:")
for k, v in r.headers.items():
    print(f"  {k}: {v}")

client.close()
