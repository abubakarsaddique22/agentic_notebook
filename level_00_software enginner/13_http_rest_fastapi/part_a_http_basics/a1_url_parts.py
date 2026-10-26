"""
A.1 URL ke hisse
================
Server ki zaroorat NAHI. Chalayein:

    python -m part_a_http_basics.a1_url_parts

Theory: part_a_http_basics/NOTES.md (A.1)
"""
import httpx

url = httpx.URL("https://api.store.com:443/v1/orders/1042?include=items&limit=5#top")

print("scheme  :", url.scheme)          # https
print("host    :", url.host)            # api.store.com
print("port    :", url.port)            # 443 (default port ho to None bhi aa sakta hai)
print("path    :", url.path)            # /v1/orders/1042
print("query   :", dict(url.params))    # {'include': 'items', 'limit': '5'}
print("fragment:", url.fragment)        # top  <- ye server tak jaata hi nahi

# ---- Khud try karein ----
# 1. Apne Shopify store ka koi product URL yahan daal kar dekhein kaunse hisse bante hain
# 2. Query mein ek aur param jorein (&sort=price) aur dobara chalayein
