"""
B.5 Path, Query, Body: data bhejne ki jagahein + URL encoding + body formats
============================================================================
    python -m part_b_methods_status_headers.b5_params_and_body

Theory: part_b_methods_status_headers/NOTES.md (B.5)
"""
import json

from common import BASE, get_client, title

client = get_client()

title("1. URL encoding: khud string jorna vs params=")
search = "watch & wallet"
print("Ghalat:", f"{BASE}/echo?q={search}")      # '&' ne URL tor diya, space bhi kharab

r = client.get("/echo", params={"q": search, "city": "لاہور", "page": 2})
print("Sahi  :", r.request.url)                  # httpx ne khud encode kiya
print("Server ko mila:", r.json()["query"])

title("2. Query params se filtering")
r = client.get("/products", params={"category": "watches", "max_price": 7000})
print(json.dumps(r.json(), indent=2))

title("3. Body ke formats: json= vs data= vs files=")
for kwargs in [{"json": {"name": "Ali"}},
               {"data": {"name": "Ali"}},
               {"files": {"file": ("notes.txt", b"Salam duniya", "text/plain")}}]:
    r = client.post("/echo", **kwargs)
    ctype = r.json()["headers"]["content-type"][:45]
    body = (r.json()["body"] or "")[:40].replace("\r\n", " ")
    print(f"{list(kwargs)[0]:<6} -> {ctype:<46} | body: {body}")

client.close()
