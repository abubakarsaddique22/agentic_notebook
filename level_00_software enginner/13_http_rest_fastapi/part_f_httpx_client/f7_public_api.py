"""
F.7 (Optional) Asli internet ki public API
==========================================
Internet ho to chalega, warna sirf message aaye ga. Practice server ki zaroorat nahi.
    python -m part_f_httpx_client.f7_public_api

curl commands: part_f_httpx_client/NOTES.md (F.7)
"""
import httpx

try:
    r = httpx.get("https://jsonplaceholder.typicode.com/posts/1", timeout=5)
    r.raise_for_status()
    print(r.status_code, r.json()["title"])
except httpx.HTTPError as e:
    print("Internet/public API tak nahi pohanch sake:", type(e).__name__)
