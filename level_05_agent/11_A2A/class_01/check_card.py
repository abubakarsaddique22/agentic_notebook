# ==========================================================
# CLASS 01 - check_card.py
# Read the Flight Agent's Agent Card (plain HTTP GET, no A2A SDK)
# Run (2nd terminal):  python check_card.py
# ==========================================================
import json

import httpx

URL = "http://127.0.0.1:9999/.well-known/agent-card.json"

card = httpx.get(URL).json()

print("Agent name   :", card["name"])
print("Description  :", card["description"])
print("Endpoint     :", card["supportedInterfaces"][0]["url"])
print("Binding      :", card["supportedInterfaces"][0]["protocolBinding"])
print("Skills       :")
for s in card["skills"]:
    print(f"  - {s['name']}  (id={s['id']})  e.g. {s['examples'][0]}")

print("\nFull card JSON:")
print(json.dumps(card, indent=2, ensure_ascii=False))
