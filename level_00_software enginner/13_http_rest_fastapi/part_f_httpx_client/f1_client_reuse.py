"""
F.1 Har baar naya connection vs Client reuse
============================================
    python -m part_f_httpx_client.f1_client_reuse

Theory: part_f_httpx_client/NOTES.md (F.1)
"""
import time

import httpx

from common import BASE, check_server

check_server()
N = 30

t = time.perf_counter()
for _ in range(N):
    httpx.get(f"{BASE}/products/1")          # har call naya connection
naya = time.perf_counter() - t

t = time.perf_counter()
with httpx.Client(base_url=BASE) as c:       # ek connection, baar baar use
    for _ in range(N):
        c.get("/products/1")
reuse = time.perf_counter() - t

print(f"Har baar naya connection: {naya * 1000:.0f} ms")
print(f"Client reuse            : {reuse * 1000:.0f} ms")
print("(Asli internet par TLS handshake ki wajah se farq kai guna zyada hota hai)")
