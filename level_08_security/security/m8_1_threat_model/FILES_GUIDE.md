# M8.1 Threat Model - Files Guide

> Is folder mein **koi code nahi**, kuch run nahi karna. Sirf parhna hai.
> Lekin aage ka har module isi ke V- aur S- numbers istemaal karta hai, is liye yeh pehle parhein.

---

## 1. Files

| File | Kaam |
|------|------|
| `README.md` | concepts: threat modeling, asset, actor, trust boundary, lethal trifecta |
| `THREAT_MODEL.md` | `app/` ka poora threat model (yahi asli file hai) |

---

## 2. THREAT_MODEL.md parhne ka order

| # | Section | Kya milega |
|---|---------|------------|
| 1 | System overview | diagram: customer -> agent -> tools -> bahar ki dunya, TB1-TB7 boundaries |
| 2 | Assets (A1-A6) | kya bachana hai: PII, paisa, internal data, prompt secret, reputation, cost |
| 3 | Actors | kaun hamla kar sakta hai: malicious customer, content attacker... |
| 4 | Trust boundaries (TB1-TB7) | kahan checking chahiye |
| 5 | Core principle | **model ka output bina-bharose hai** |
| 6 | Lethal trifecta | teeno cheezein `app/` mein mojood hain |
| 7 | Vulnerabilities (V1-V11) | har kamzori + kaunsi file + kaun sa module theek karega |
| 8 | Attack scenarios (S1-S8) | attacks jo M8.2 / M8.7 mein chalenge |
| 9 | Defence plan | module wise kaun kya band karega |

---

## 3. Numbers ko code se jorna

| ID | Code mein kahan dhoondein |
|----|---------------------------|
| V1, V7, V9, V11 | `app/agent.py` (comments mein `VULN V1` waghera likha hai) |
| V2, V3, V4, V6, V8 | `app/tools.py` |
| V5 | `app/knowledge_base.py` -> `search()` |
| S1-S6 | `m8_2_prompt_injection/attacks.py` -> `ATTACKS` list (`id` mein S-number) |

| Kamzori | Theek kahan hoti hai |
|---------|----------------------|
| V1 secret in prompt | `m8_9_capstone/secure_agent.py` (prompt se hata diya) |
| V2 BOLA, V4 refund | `m8_4_agent_security/authz.py` |
| V3 email | `m8_2/defended_agent.py` (allow-list), `m8_4/authz.py` |
| V5 internal docs, V6 | `m8_5_rag_security/secure_retrieval.py` (+ `m8_2/defenses.py` fence) |
| V7 guardrails | `m8_3_guardrails/` |
| V8 PII | `m8_6_privacy_pii/pii.py` (m8_9 mein use) |
| V9 limits | `m8_4_agent_security/limits.py` |
| V10 audit | `m8_6/safe_logging.py`, `m8_8_governance/` |
| V11 | `m8_2` dikhata hai ke prompt wali "defence" fail hoti hai |

---

## 4. Yaad rakhne ki baat

- S7 (jailbreak) aur S8 (tool loop) table mein hain lekin `attacks.py` ki list mein **nahi**.
  `ATTACKS` mein sirf S1-S6 hain.
- Threat model mein Llama Guard likha hai, lekin asal code (M8.3) `gpt-oss:20b-cloud` se moderation karta hai.
