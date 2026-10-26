# M8.6 - Data Privacy, PII & Secrets

## Pehle concepts samajh lein

- **PII (Personally Identifiable Information)**: zaati maloomat jis se banda
  pehchana ja sake, jaise naam, phone, address, email, CNIC, card number.

- **Sensitive data**: PII ke ilawa credentials (passwords/keys), financial data,
  private conversations, aur business ka confidential data.

- **Redaction / masking**: sensitive hisse ko chhupa dena, jaise
  "Ali Raza, 0300-0000001" ko "<PERSON>, <PK_PHONE>" bana dena.

- **Data minimisation**: model/log ko sirf utna data do jitna waqai chahiye.
  Poora PII bhejne ki zaroorat nahi to mat bhejo.

- **PII out of logs/traces**: logs, traces, memory, vector store, aur eval
  datasets sensitive data ki doosri copy na ban jayein. Log karne se pehle redact.

- **Secret**: koi raaz jaise API key, token, password. Model ko kabhi beloujah na
  dikhao; agar leak ho gaya to bara nuqsan.

- **Retention / deletion / residency**: data kitni dair rakha jata hai, kaise
  delete hota hai, aur kis mulk mein store hota hai.

- **Third-party model provider ka masla**: jab aap kisi cloud model (jaise Groq)
  ko prompt bhejte hain to aap ka data us provider tak jata hai. Isi liye:
  - **Zero-retention / no-training terms**: contract jisme likha ho ke provider
    aap ka data na rakhega na us par train karega.
  - **Private connectivity**: public internet ke bajaye private raaste se
    model tak pohanchna (regulated deployments ke liye).

## Files

| File | Kaam |
|------|------|
| `pii.py` | Presidio se PII redaction; Pakistan ke phone + CNIC recognizers; poora local chalta hai |
| `secrets_scan.py` | regex + detect-secrets se API keys, tokens, passwords pakarna |
| `safe_logging.py` | ek logger jo likhne se pehle PII redact aur secret scrub karta hai |

## Prompt ka secret theek karna (V1)

Manager coupon pehle system prompt mein tha. Secure agent (M8.9) mein usay poora
hata diya hai, kyun ke jo cheez model ko dikhti hi nahi, woh koi jailbreak leak
nahi kar sakta. Jo secrets tools ko chahiye woh `.env` mein rehte hain, code
parhta hai, kabhi prompt mein nahi.

## Data minimisation (V8)

`get_order` poora PII model ko de deta tha. Secure agent order data ko
`pii.redact()` se saaf karta hai pehle ke woh context mein jaye, to model ko asli
naam/address ke bajaye "<PERSON> at <LOCATION>" dikhta hai.

## Provider wali baat

Groq free tier par zero-retention / no-training ka koi contract nahi. Is liye:
sirf nakli data, aur asli regulated deployment ke liye aisa provider tier ya
self-hosted model chahiye jo private connectivity aur zero-retention de. Yeh baat
model card (M8.8) mein likhi hai.

## Chalana (Windows PowerShell)

```powershell
cd C:\Users\abubakar\Desktop\security
.venv\Scripts\activate
pip install presidio-analyzer presidio-anonymizer spacy detect-secrets
python -m spacy download en_core_web_lg

python -m m8_6_privacy_pii.pii
python -m m8_6_privacy_pii.secrets_scan
python -m m8_6_privacy_pii.safe_logging
```
