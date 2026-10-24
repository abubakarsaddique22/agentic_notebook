"""
Chalte hue store_api server ko asli HTTP requests bhejo.

Terminal 1 (isi folder mein):  uvicorn app.main:app --reload --port 8767
Terminal 2 (isi folder mein):  python try_api.py
"""
import os
import time

import httpx

os.environ["NO_PROXY"] = "127.0.0.1,localhost"
API = "http://127.0.0.1:8767"
K = {"X-API-Key": "dev-key-2"}

try:
    with httpx.Client(base_url=API, timeout=10) as c:
        print(c.get("/v1/health").json())
        print(c.get("/v1/orders/1042", headers=K).json())
        print(c.get("/v1/orders/1042").json(), "<- bina key")
        t = time.perf_counter()
        print(c.post("/v1/chat", json={"message": "Return policy kya hai?"}, headers=K).json(),
              f"({time.perf_counter() - t:.2f}s, asli FakeLLM)")
        print(f"\nBrowser mein kholein: {API}/docs")
except httpx.ConnectError:
    print("Server nahi chal raha. Pehle chalayein:  uvicorn app.main:app --reload --port 8767")
