# M8.7 - Red Teaming AI Systems

## Pehle concepts samajh lein

- **Red teaming**: jaan boojh kar apni hi app par hamla karna taake kamzoriyan
  attacker se pehle khud dhoond lein. Jaise LLM ka "penetration testing".

- **Adversarial test suite**: attacks ka ek majmooa (injection, jailbreaks,
  malicious documents, tool misuse, data extraction, unsafe actions) jo baar baar
  chalaya ja sakay.

- **RAG ko corpus se attack karna**: retrieve hone wale documents mein bura content
  daal kar dekhna ke model gumraah hota hai ya nahi (retrieval poisoning test).

- **Agent ko tools se attack karna**: koshish karna ke agent apni ijazat se aage
  nikal jaye, tool ka ghalat istemaal kare, secret ugle, ya loop mein phas jaye.

- **Vulnerability -> regression test**: jo kamzori mile, usay ek permanent test
  bana do taake aainda koi tabdeeli usay dobara na khol de (hamesha green rahe).

- **Attack Success Rate (ASR)**: kamyab attacks ÷ total attacks. Jitna kam utna
  behtar. Insecure vs secure ka ASR compare karna progress ka saboot hai.

- **Leakage rate / unsafe-action rate**: kitni baar sensitive data leak hua ya
  koi khatarnak action hua. Inhe bhi naapa jata hai.

## Do tareeqe, dono muft

1. `attack_suite.py` - **apna harness**. Saare M8.2 attacks ko insecure aur
   secure agent par chalata hai, side-by-side table chhapta hai, **ASR** nikalta
   hai, aur `outputs/redteam_report.json` save karta hai. Koi extra install nahi.
   Yahi pehle chalayein.

2. `deepteam_redteam.py` - **DeepTeam** (Confident AI, wahi family jis ka
   DeepEval tha jo aap ne Level 7 mein use kiya). Yeh khud attacks banata hai bohat
   si vulnerability qismon ke liye. Attacker aur judge aap ke local Ollama model
   (gpt-oss:20b-cloud) par chalte hain, to na OpenAI key, na kharcha.

Kamzori-ko-test-banana wala step `tests/security/` (M8.9) mein hai: har attack jo
kabhi kamyab hua, woh ek pytest ban jaata hai jo hamesha pass rehna chahiye.

## Chalana (Windows PowerShell)

```powershell
cd C:\Users\abubakar\Desktop\security
.venv\Scripts\activate

# apna harness (ASR insecure vs secure):
python -m m8_7_red_teaming.attack_suite --no-model-guard

# DeepTeam (optional, zyada bhaari):
pip install deepteam
deepeval set-ollama --model gpt-oss:20b-cloud
python -m m8_7_red_teaming.deepteam_redteam
```

Umeed: insecure ka ASR zyada, secure ka ASR bohat kam. Jo attack secure agent par
abhi bhi HIT ho, woh aap ka agla kaam hai, usay theek karo, phir woh ek test ban
jaye.
