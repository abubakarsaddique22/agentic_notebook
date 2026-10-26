"""
Saare orchestration scenarios bina server chalaye (FastAPI TestClient se).

    python 07_pipeline_orchestration\\try_app.py

Default: MOCK LLM (agar GROQ_API_KEY .env mein hai to Groq). Force mock: set LLM_MODE=mock
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fastapi.testclient import TestClient  # noqa: E402

from app import app  # noqa: E402

c = TestClient(app)
print("health:", c.get("/health").json())

print("\n=== 1) SYNC /chat: deterministic routing (dekho kahan LLM laga, kahan nahi) ===")
for text in ["Salam", "Return policy kya hai?", "Mera order #12345 kahan hai?",
             "Order #99999 ka status?", "Mujhe manager se baat karni hai",
             "Kya aap ke paas blue dial hai?"]:
    r = c.post("/chat", json={"text": text}).json()
    steps = " -> ".join(f"{s['step']}({s['ms']}ms)" for s in r["steps"])
    print(f"  {text!r:38} intent={r['intent']:<13} route={r['route']}")
    print(f"  {'':38} steps: {steps or '-'} | total {r['total_ms']}ms")
    print(f"  {'':38} reply: {r['reply'][:80]!r}")

print("\n=== 2) WhatsApp webhook: fast ACK + background + idempotency ===")
msg = {"message_id": "wamid.ABC123", "from_number": "923001234567", "text": "Delivery kitne din?"}
print("  first delivery :", c.post("/webhook/whatsapp", json=msg).json())
print("  Meta retry (same id):", c.post("/webhook/whatsapp", json=msg).json())
print("  outbox (sirf EK reply gaya):", c.get("/outbox").json())

print("\n=== 3) Long-running job: 202 + polling ===")
j = c.post("/reports", json={"kind": "unanswered_questions"})
print("  create:", j.status_code, j.json())
print("  poll  :", c.get(j.json()["poll"]).json())
