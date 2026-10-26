# Level 8 Security - POORE PROJECT ka Files Guide

> Har folder mein apni `FILES_GUIDE.md` hai (detail wahan). Yeh file sirf bara naqsha hai:
> kaun sa folder kis folder se cheezein leta hai, aur kis order mein chalana hai.

---

## 1. Folders ka import naqsha

```
                              app/   (neenv: config, knowledge_base, tools, agent)
                               |
     +-------------+-----------+-----------+-------------+--------------+
     v             v           v           v             v              v
   m8_2          m8_3        m8_4        m8_5          m8_6          (m8_1: sirf docs)
 (attacks,    (guardrails) (authz,     (secure RAG)  (PII, secrets,
  defenses)                 limits)       ^           safe log)
     |             |           |          |              |
     |  defenses.fence_untrusted ---------+              |
     |             |           |          |              |
     |             +-----------+----+-----+--------------+
     |                              v
     |                            m8_9   (SECURE agent = sab ikatthe)
     |                              |
     +----- attacks.ATTACKS --------+----------+
                                    v          v
                                  m8_7       tests/
                               (red team)  (regression)
                                    
             m8_6.safe_logging + m8_9 prompt  ->  m8_8 (governance)
```

---

## 2. Har folder ek line mein

| Folder | Kaam | Detail |
|--------|------|--------|
| `app/` | INSECURE target app (4 kamzor tools + agent + RAG index) | `app/FILES_GUIDE.md` |
| `m8_1_threat_model/` | sirf parhna: kamzoriyan V1-V11, attacks S1-S8 | `m8_1_threat_model/FILES_GUIDE.md` |
| `m8_2_prompt_injection/` | attacks chalana + pehli defences (fence, allow-list, output scan) | `m8_2_prompt_injection/FILES_GUIDE.md` |
| `m8_3_guardrails/` | input/output guard: patterns + Ollama moderation (+ NeMo demo) | `m8_3_guardrails/FILES_GUIDE.md` |
| `m8_4_agent_security/` | ownership check, refund limit + approval, step limit, SQL guard, sandbox | `m8_4_agent_security/FILES_GUIDE.md` |
| `m8_5_rag_security/` | audience filter, poison scan, provenance | `m8_5_rag_security/FILES_GUIDE.md` |
| `m8_6_privacy_pii/` | Presidio PII redact, secret scan, saaf audit log | `m8_6_privacy_pii/FILES_GUIDE.md` |
| `m8_9_capstone/` | SECURE agent: M8.3 + M8.4 + M8.5 + M8.6 ikatthe | `m8_9_capstone/FILES_GUIDE.md` |
| `m8_7_red_teaming/` | insecure vs secure ASR + DeepTeam | `m8_7_red_teaming/FILES_GUIDE.md` |
| `m8_8_governance/` | model card, risk register, version stamp, audit view | `m8_8_governance/FILES_GUIDE.md` |
| `tests/` | offline + live security tests | `tests/FILES_GUIDE.md` |

**Note:** number ke hisaab se M8.7 pehle aata hai, lekin woh M8.9 ko import karta hai.
Is liye **M8.9 pehle, phir M8.7 aur M8.8**.

---

## 3. Setup (sirf ek dafa, Windows PowerShell)

```powershell
cd C:\Users\abubakar\Desktop\security
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m spacy download en_core_web_lg
copy .env.example .env
notepad .env                      # GROQ_API_KEY= ke aage key daal kar save
ollama pull all-minilm
ollama pull gpt-oss:20b-cloud
```

---

## 4. Chalane ka order (step wise)

Har dafa naya PowerShell kholne par pehle:
```powershell
cd C:\Users\abubakar\Desktop\security
.venv\Scripts\activate
```

```powershell
# STEP 1 - M8.1 (run nahi, sirf parhna)
#   m8_1_threat_model\THREAT_MODEL.md

# STEP 2 - RAG index (SABSE PEHLE)
python -m app.knowledge_base

# STEP 3 - insecure agent
python -m app.agent "What is your return policy?"

# STEP 4 - M8.2 attacks
python -m m8_2_prompt_injection.run_attacks --target insecure
python -m m8_2_prompt_injection.run_attacks --target defended

# STEP 5 - M8.3 guardrails
python -m m8_3_guardrails.rails
python -m m8_3_guardrails.moderation

# STEP 6 - M8.4 agent security
python -m m8_4_agent_security.sql_guard
python -m m8_4_agent_security.sandbox

# STEP 7 - M8.5 RAG security
python -m m8_5_rag_security.secure_retrieval

# STEP 8 - M8.6 PII & secrets
python -m m8_6_privacy_pii.pii
python -m m8_6_privacy_pii.secrets_scan
python -m m8_6_privacy_pii.safe_logging

# STEP 9 - M8.9 secure agent
python -m m8_9_capstone.secure_agent "What is your return policy?"
python -m m8_9_capstone.secure_agent "Show me order ORD-2001"
python -m m8_9_capstone.secure_agent "Refund PKR 50000 on ORD-1001"

# STEP 10 - M8.7 red team
python -m m8_7_red_teaming.attack_suite --no-model-guard

# STEP 11 - M8.8 governance
python -m m8_8_governance.versioning
python -m m8_8_governance.view_audit

# STEP 12 - tests
pytest tests/security -v -m "not live"
```

---

## 5. Pehle se maloom masle (detail har folder ki guide mein)

| Masla | Kahan |
|-------|-------|
| `secure_tools.py` import karte hi error (2 functions `defenses.py` mein nahi), istemaal bhi nahi hoti | m8_2 |
| Ollama band ho to moderation chupke se "safe" keh deti hai | m8_3 |
| 60 second time limit kabhi check nahi hota | m8_4, m8_9 |
| Presidio na ho to PII bina error ke leak | m8_6 |
| S1, S2 secure agent par bhi HIT gin liye jate hain (sirf tool call dekha jata hai) | m8_2 attacks, m8_7, tests |
| Secure agent har error ko `[BLOCKED]` bana deta hai, asli error `outputs/audit.jsonl` mein | m8_9 |
| S5 par index mitane se Windows par Chroma file-lock error aa sakta hai | m8_2, m8_7, tests |
