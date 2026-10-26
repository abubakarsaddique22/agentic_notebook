"""
B.6 Cookies: httpx.Client browser ki tarah cookies yaad rakhta hai
=================================================================
    python -m part_b_methods_status_headers.b6_cookies

Theory: part_b_methods_status_headers/NOTES.md (B.6)
"""
import httpx

from common import BASE, check_server

check_server()

with httpx.Client(base_url=BASE) as browser_jaisa:
    print("Login se pehle:", browser_jaisa.get("/me").status_code, "(401: cookie nahi)")
    r = browser_jaisa.post("/login")
    print("Set-Cookie    :", r.headers["set-cookie"])
    print("Login ke baad :", browser_jaisa.get("/me").json(), "(client ne cookie khud bheji)")

# Naya client = naya 'browser' = koi cookie nahi
print("Naya client   :", httpx.get(f"{BASE}/me").status_code)
