# M8.6 Privacy, PII & Secrets - Files Guide (kaun si file kya karti hai, kaun kis ko import karti hai)

> Yahan class inheritance nahi, sirf `from x import y` wala import hai.

---

## 1. Import ka naqsha

```
      pii.py                  secrets_scan.py            app/config.py
 (Presidio, koi project    (regex + detect-secrets,      (OUTPUT_DIR)
  import nahi)              koi project import nahi)          |
        |                          |                          |
        +-------------+------------+--------------------------+
                      v
               safe_logging.py      (log likhne se pehle redact + scan)
                      |
        +-------------+------------------------+
        v                                      v
 m8_9_capstone/secure_agent.py        m8_8_governance/view_audit.py
 (log_event, aur pii.redact bhi)      (LOG_FILE parhta hai)

 tests/security/test_unit_defenses.py  ->  secrets_scan.has_secret
```

---

## 2. Parhne ka order

| # | File | Kyun |
|---|------|------|
| 1 | `pii.py` | kisi pe depend nahi, PII chhupana |
| 2 | `secrets_scan.py` | kisi pe depend nahi, keys / passwords pakarna |
| 3 | `safe_logging.py` | 1 + 2 ko jor kar saaf log likhna |

---

## 3. Har file ka kaam

### `pii.py`
- `Redaction` -> dataclass: `text` (chhupaya hua) + `found` (kya kya mila)
- `_engines()` -> Presidio ke 2 engine banata hai (`@lru_cache`, sirf pehli dafa, slow hai):
  - `AnalyzerEngine` -> PII **dhoondta** hai
  - `AnonymizerEngine` -> PII **chhupata** hai (`Ali` -> `<PERSON>`)
  - 2 Pakistani recognizers add: `PK_PHONE` (03XX-XXXXXXX), `PK_CNIC` (12345-1234567-1)
- `DEFAULT_ENTITIES` -> PERSON, EMAIL, PHONE, LOCATION, CREDIT_CARD, IBAN, PK_PHONE, PK_CNIC
- `redact(text)` -> analyze -> anonymize -> `Redaction`

### `secrets_scan.py`
- `_PATTERNS` -> regex: Groq key (`gsk_`), OpenAI (`sk-`), AWS (`AKIA`), bearer token, `password=...`
- `scan(text)` -> mile hue secrets ki qisam ki list. `detect-secrets` installed ho to woh bhi chalta hai
- `has_secret(text)` -> `scan` khaali nahi to True

### `safe_logging.py`
| Kahan se | Kya liya |
|----------|----------|
| `app.config` | `OUTPUT_DIR` |
| `m8_6_privacy_pii.pii` | `redact` |
| `m8_6_privacy_pii.secrets_scan` | `scan` |

- `LOG_FILE` -> `outputs/audit.jsonl`
- `_clean(value)` -> string ho to: secret mile to **poora** text `[REDACTED-SECRET]`, phir `redact`.
  dict / list ho to andar har cheez par khud ko dobara chalata hai (recursion)
- `log_event(event, **fields)` -> `{ts, event, ...saaf fields}` ek line `audit.jsonl` mein

### `__init__.py`
Khaali. Folder ko package banata hai.

---

## 4. Chalana aur andar kya hota hai

```powershell
pip install presidio-analyzer presidio-anonymizer spacy detect-secrets
python -m spacy download en_core_web_lg

python -m m8_6_privacy_pii.pii             # Ali ka sample text redact
python -m m8_6_privacy_pii.secrets_scan    # 3 samples scan
python -m m8_6_privacy_pii.safe_logging    # ek saaf audit line likhta hai
```

```
log_event("tool_call", tool="get_order", result="Ali Raza, 0300-0000001, key gsk_...")
   |
   v
_clean(fields)
   tool   = "get_order"                -> scan: saaf -> redact -> "get_order"
   result = "Ali Raza, ... gsk_..."    -> scan: groq_key mila -> "[REDACTED-SECRET]"
   |
   v
outputs/audit.jsonl  mein likha
```

---

## 5. Aage kahan kaam aati hain

| File | Kaun import karta hai |
|------|-----------------------|
| `pii.py` | `m8_9/secure_agent.py` (`redact`, order ke PII fields par), `safe_logging.py` |
| `secrets_scan.py` | `safe_logging.py`, tests (`has_secret`) |
| `safe_logging.py` | `m8_9/secure_agent.py` (`log_event`), `m8_8/view_audit.py` (`LOG_FILE`) |

---

## 6. Yaad rakhne ki baat

- **Presidio install na ho to `redact()` text waisa hi chhor deta hai** (`found=["[presidio-not-installed]"]`).
  Yani bina error ke PII leak. Is liye Presidio aur `en_core_web_lg` zaroor install karein.
- Secret milne par `_clean` sirf secret nahi, **poora** string `[REDACTED-SECRET]` kar deta hai.
- Prompt ka secret (V1) yahan theek nahi hota. Woh `m8_9/secure_agent.py` mein prompt se hata kar theek hua.
