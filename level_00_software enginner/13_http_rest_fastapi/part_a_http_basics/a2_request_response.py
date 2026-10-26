"""
A.2 Request/Response cycle: apni aankhon se dekhein
===================================================
Pehle server chalayein (doosri cmd window):
    uvicorn practice_server:app --port 8765 --reload
Phir:
    python -m part_a_http_basics.a2_request_response

Theory: part_a_http_basics/NOTES.md (A.2)
"""
from common import get_client, show, title

client = get_client()

title("Raw HTTP: request aur response ke saare hisse")
r = client.get("/products/1")
show(r)

title("Python mein response ke hisse")
print("Status code :", r.status_code)          # 200
print("Success?    :", r.is_success)           # 2xx hai?
print("Content-Type:", r.headers["content-type"])
data = r.json()                                # JSON body -> Python dict
print("Data        :", data)
print("Price       :", data["price"])
print("Time liya   :", round(r.elapsed.total_seconds() * 1000, 1), "ms")

client.close()
