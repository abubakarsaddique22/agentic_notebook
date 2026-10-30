# ==========================================================
# CLASS 01 - raw_jsonrpc_call.py
# Talk to the Flight Agent WITHOUT the A2A client.
# This shows what really travels on the wire: a JSON-RPC message.
# Run (2nd terminal):  python raw_jsonrpc_call.py
# ==========================================================
import json
import uuid

import httpx

payload = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "SendMessage",            # <- the operation name lives INSIDE the JSON
    "params": {
        "message": {
            "messageId": str(uuid.uuid4()),
            "role": "ROLE_USER",
            "parts": [{"text": "Find flights from Bangalore to Dubai"}],
        }
    },
}

response = httpx.post(
    "http://127.0.0.1:9999/",
    json=payload,
    headers={"A2A-Version": "1.0"},     # without this header the server says: version '0.3' not supported
)

data = response.json()
print("RAW RESPONSE:")
print(json.dumps(data, indent=2, ensure_ascii=False))

print("\nJUST THE TEXT:")
print(data["result"]["message"]["parts"][0]["text"])
