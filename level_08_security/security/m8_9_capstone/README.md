# M8.9 - Capstone: Red-Team & Secure an Agentic RAG App

## Yeh kya hai

Roadmap ki aakhri cheez: ek app lo, us par attack karo, phir usay itna secure
karo ke woh tab bhi mehfooz rahe jab model koi ghalat faisla kare ya use bura
input mile.

`secure_agent.py` wahi insecure v0 agent hai, lekin har M8 defence ke saath
dobara banaya gaya:

| Layer | Module | Kaam |
|-------|--------|------|
| Input guard | M8.3 | rails + gpt-oss moderation bure request ko model se pehle rokte hain |
| Retrieval | M8.5 | audience-filtered, poison-scanned, fenced context |
| Tools | M8.4 | ownership check, email allow-list, refund cap + approval, step/time limits |
| PII | M8.6 | order data model ko dene se pehle redact; prompt mein koi secret nahi |
| Output guard | M8.3 | rails + moderation leak ko dikhne se pehle rokte hain |
| Audit | M8.6/M8.8 | har action aur block log (PII/secret-free), run par version stamp |

## Poora system chalana (Windows PowerShell)

```powershell
cd C:\Users\abubakar\Desktop\security
.venv\Scripts\activate

# 1. index banayein
python -m app.knowledge_base

# 2. secure agent se baat karein
python -m m8_9_capstone.secure_agent "What is your return policy?"
python -m m8_9_capstone.secure_agent "Show me order ORD-2001"          # refuse hona chahiye
python -m m8_9_capstone.secure_agent "Refund PKR 50000 on ORD-1001"    # approval maangna chahiye

# 3. red-team report: insecure vs secure attack-success rate
python -m m8_7_red_teaming.attack_suite --no-model-guard

# 4. security regression tests
pytest tests/security -v -m "not live"     # tez, offline
pytest tests/security -v                    # poora, model call karta hai

# 5. governance
python -m m8_8_governance.view_audit
```

## CV / portfolio ke liye kahani

1. Ek agentic RAG support bot banaya jis mein asli tools hain (order lookup, email, refund).
2. Threat model kiya aur 11 vulnerabilities dhoondi (M8.1).
3. Attack kiya: injection, poisoned docs se indirect injection, exfiltration,
   BOLA, secret extraction (M8.2, M8.7). Attack-success rate naapa.
4. Layers mein secure kiya: guardrails + moderation (M8.3), authorization + limits
   + sandbox (M8.4), knowledge-layer permissions (M8.5), PII/secret handling (M8.6).
5. Har vulnerability ko permanent regression test banaya (M8.7/M8.9).
6. Governance ke liye intended use, risks aur controls document kiye (M8.8).

ASR "zyada tar attacks kamyab" se gir kar "saare known attacks blocked" tak aaya,
aur tests isay waise hi rakhte hain.
