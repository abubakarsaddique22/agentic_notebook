# M8.3 - Jailbreaks, Guardrails & Moderation

## Pehle concepts samajh lein

- **Jailbreak**: model se us ki apni safety/policy ttorwana, jaise usay manwana
  ke woh koi mana kiya hua ya nuqsan-deh jawab de de ("tum ab ek bina rok-tok
  wale AI ho...", "developer mode on karo" waghera).

- **Jailbreak vs Injection**:
  - Injection = model ke *instructions* badalna (attacker ka kaam karwana).
  - Jailbreak = model ki *safety* torna (mana cheez karwana).
  - Aksar dono ek saath istemaal hote hain, lekin concept alag hai.

- **Guardrail**: model ke aage (input) aur peeche (output) lagi checking layer
  jo bure message ya bure jawab ko rok de.

- **Input guardrail**: user ka message model tak jaane se pehle check hota hai.
- **Output guardrail**: model ka jawab user ko dikhne se pehle check hota hai.

- **Moderation**: kisi message ko "safe / unsafe" classify karna (violence, hate,
  self-harm, sexual, illegal, ya secret/PII nikalne ki koshish).

- **Obfuscation**: attack ko chhupane ki koshish taake simple check pakar na
  sakay, jaise `i g n o r e` (spaces), `1gn0re` (leetspeak), ya unicode tricks.
  Isi liye guardrails ko aise ghuma-phira ke input par bhi test karna zaroori hai.

- **Defence in depth (kai layers)**: ek guardrail kaafi nahi. Pattern-check nayi
  phrasing miss karti hai; model-based check slow hai aur dhoka kha sakta hai;
  dono mil kar behtar hain.

## Do layers (sabse sasti pehle)

1. `rails.py` - **deterministic pattern checks**. Muft, foran, kabhi galat nahi
   batata (no hallucination). Is mein `normalize()` hai jo match karne se PEHLE
   obfuscation hata deta hai (spaces, leetspeak, zero-width/unicode). Yahi
   "obfuscated input par test" wala point hai.

2. `moderation.py` - **gpt-oss:20b-cloud** ko (Ollama par) ek sakht safe/unsafe
   classifier bana kar istemaal karta hai. Wahi model jo Level 7 ka judge tha, to
   kuch naya pull nahi karna. (Llama Guard ek purpose-built alternative hai agar
   kabhi dedicated classifier chahiye ho.)

`guardrail_layer.py` dono ko mila kar `guard_input()` / `guard_output()` banata
hai, jinhe secure agent (M8.9) har turn ke aage-peeche lagata hai.

## NeMo Guardrails (roadmap ka named framework)

`nemo_config/` mein ek chalne wala NeMo config hai jo LOCAL Ollama model
(gpt-oss:20b-cloud) par chalta hai, koi NVIDIA key nahi. Yeh sirf reference hai
taake framework samajh aa jaye; asli agent halka custom layer use karta hai kyun
ke woh Windows par tez aur aasaan hai. (Us folder ki files mein tafseeli Roman
Urdu comments likhe hain.)

## Chalana (Windows PowerShell)

```powershell
cd C:\Users\abubakar\Desktop\security
.venv\Scripts\activate

python -m m8_3_guardrails.rails          # obfuscation handling dekhein
python -m m8_3_guardrails.moderation     # gpt-oss ka safe/unsafe classify dekhein

# optional, NeMo framework khud (gpt-oss:20b-cloud use karta hai):
pip install nemoguardrails
python -m m8_3_guardrails.nemo_demo
```

## Ek layer kyun kaafi nahi

- Patterns nayi phrasing aur asli harmful content miss karte hain -> model chahiye.
- Model slow hai, call ka kharcha hai, aur chalaaki se dhoka kha sakta hai -> patterns + code chahiye.
- Koi bhi yeh nahi samajhta ke "yeh order kisi aur ka hai" -> woh authorization hai (M8.4).

Guardrails farsh uncha karte hain. Woh kabhi poori deewar nahi hote.
