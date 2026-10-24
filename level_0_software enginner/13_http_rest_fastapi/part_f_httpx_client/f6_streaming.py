"""
F.6 Streaming response (SSE): ChatGPT jaisa token by token
==========================================================
    python -m part_f_httpx_client.f6_streaming

Theory: part_f_httpx_client/NOTES.md (F.6)
"""
from common import get_client

client = get_client()

with client.stream("GET", "/stream", params={"prompt": "Salam"}) as r:
    print("Content-Type:", r.headers["content-type"])
    for line in r.iter_lines():                 # har line aate hi milti hai
        if line.startswith("data: "):
            token = line[len("data: "):]
            if token == "[DONE]":
                break
            print(token, end=" ", flush=True)    # flush: foran screen par
print()
client.close()
