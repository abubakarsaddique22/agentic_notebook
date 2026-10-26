# M8.8 Governance - Files Guide (kaun si file kya karti hai, kaun kis ko import karti hai)

> Yahan class inheritance nahi, sirf `from x import y` wala import hai.
> Do files sirf parhne ki hain (.md), do Python files hain.

---

## 1. Import ka naqsha

```
   app/config.py (GROQ_MODEL)        m8_9/secure_agent.py (SECURE_SYSTEM_PROMPT)
            |                                  |  (sirf __main__ mein)
            +----------------+-----------------+
                             v
                       versioning.py


   m8_6_privacy_pii/safe_logging.py (LOG_FILE = outputs/audit.jsonl)
                             |
                             v
                       view_audit.py


   MODEL_CARD.md, RISK_REGISTER.md   -> koi import nahi, sirf documents
```

---

## 2. Parhne ka order

| # | File | Kyun |
|---|------|------|
| 1 | `MODEL_CARD.md` | app kis kaam ki hai, kis ki nahi, risks, privacy |
| 2 | `RISK_REGISTER.md` | har risk (R1-R11) + control + bacha hua risk |
| 3 | `versioning.py` | run ka version stamp |
| 4 | `view_audit.py` | audit log ka khulasa |

---

## 3. Har file ka kaam

### `MODEL_CARD.md`
Intended use, not intended for, models, limitations, human oversight (5000 se upar refund),
data & privacy (Groq free tier par asli PII nahi), evaluations, versioning, regulatory note
(EU AI Act limited-risk, Pakistan PDPB).

### `RISK_REGISTER.md`
R1-R11 table: risk, asset, likelihood / impact (L/M/H), control (kaun sa module), residual.
Neeche "accepted residual risks" (R7, R11 poori tarah khatam nahi).

### `versioning.py`
| Kahan se | Kya liya |
|----------|----------|
| `app.config` | `GROQ_MODEL` |
| `m8_9_capstone.secure_agent` | `SECURE_SYSTEM_PROMPT` (sirf jab file khud chale) |

- `PROMPT_VERSION = "secure-v1"`, `DEFENSE_CONFIG_VERSION = "m8-full-v1"`
- `prompt_fingerprint(prompt)` -> prompt ka SHA-256 hash (12 akshar). Prompt chupke se badle
  to hash badal jayega
- `run_stamp(prompt)` -> `{prompt_version, prompt_sha, model, defense_config}`

### `view_audit.py`
| Kahan se | Kya liya |
|----------|----------|
| `m8_6_privacy_pii.safe_logging` | `LOG_FILE` |

- `main()` -> `audit.jsonl` parh kar: har event kitni dafa (`Counter`), aur aakhri 10
  `_blocked` events (input_blocked, output_blocked)

### `__init__.py`
Khaali. Folder ko package banata hai.

---

## 4. Chalana aur andar kya hota hai

```powershell
python -m m8_8_governance.versioning     # version stamp JSON
python -m m8_8_governance.view_audit     # PEHLE m8_9 secure agent kuch dafa chalayein
```

```
m8_9 secure_agent chalta hai
   -> har tool call / block par safe_logging.log_event()
   -> outputs/audit.jsonl mein saaf line
                    |
                    v
view_audit.main()  -> ginti + blocked events print
```

---

## 5. Aage kahan kaam aati hain

Koi file isay import nahi karti. Yeh "saboot" wala hissa hai.

---

## 6. Yaad rakhne ki baat

- `versioning.run_stamp()` sirf print hota hai, **audit log mein khud nahi likha jata**
  (m8_9 isay call nahi karta). Model card yeh kehta hai ke har run stamp hota hai, code abhi nahi karta.
- Model card mein moderation "Llama Guard 3" likha hai, asal code `gpt-oss:20b-cloud` use karta hai.
- `view_audit` ko kuch dikhane ke liye pehle `m8_6.safe_logging` ya `m8_9.secure_agent` chalna zaroori hai.
