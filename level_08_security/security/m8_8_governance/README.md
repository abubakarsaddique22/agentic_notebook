# M8.8 - Responsible AI & Governance

## Pehle concepts samajh lein

- **Responsible AI**: AI ko is tarah banana aur chalana ke woh mehfooz, munsifana
  aur shaffaf ho.

- **Hallucination**: model ka ghalat baat ko yaqeen se sach ki tarah keh dena.

- **Bias / fairness**: model kisi group ke saath ghair-munsifana bartao na kare.

- **Transparency**: user ko bata dena ke woh AI se baat kar raha hai, aur system
  kaise faisle karta hai.

- **Accountability**: agar kuch ghalat ho to zimmedari aur sudhaar ka raasta ho.

- **Human oversight**: ahem/khatarnak faislon par insaan ki nigraani ya manzoori.

- **Model card**: ek document jo batata hai: app kis kaam ke liye hai, kis ke liye
  nahi, kaun se models, kya limits aur risks, aur insaani control kahan hai.

- **Risk register**: har risk ki list, us ka control (ilaaj), aur control ke baad
  bacha hua risk (residual).

- **Auditability**: baad mein yeh saabit kar sakna ke kaunsa prompt, kaunsa model,
  aur kaunsa config kis faisle ke peeche tha. Is ke liye prompt/model versions,
  logs, approvals aur eval records rakhe jaate hain.

- **Regulations (practical asar)**:
  - **EU AI Act**: Europe ka AI qanoon; app ko risk level ke hisaab se rules.
    Customer-facing support bot aam tor par "limited risk" hai -> transparency +
    logging ki zaroorat.
  - **India DPDP / Pakistan PDPB**: data protection qanoon jo PII ke istemaal ko
    control karte hain.

## Files

| File | Kya hai |
|------|---------|
| `MODEL_CARD.md` | intended use, limits, risks, data/privacy, regulatory note |
| `RISK_REGISTER.md` | har risk, us ka control, aur control ke baad bacha risk |
| `versioning.py` | har run par prompt version + prompt hash + model + defence config stamp karta hai |
| `view_audit.py` | saaf (PII/secret-free) audit log ka khulasa dikhata hai |

## Point

Security controls (M8.2-M8.7) "kaise" hain. Governance "kya hum saabit kar sakte
hain" hai: kaun use kar sakta hai, kya nahi karna chahiye, fail hone par kya
hota hai, aur ek record jis se purana faisla audit ho sake. Asli store ke liye
yeh woh documents hain jo aap kisi partner, payment provider, ya regulator ko
dikhayenge.

## Chalana (Windows PowerShell)

```powershell
cd C:\Users\abubakar\Desktop\security
.venv\Scripts\activate
python -m m8_8_governance.versioning     # run stamp dekhein
python -m m8_8_governance.view_audit     # secure agent chalane ke baad
```
