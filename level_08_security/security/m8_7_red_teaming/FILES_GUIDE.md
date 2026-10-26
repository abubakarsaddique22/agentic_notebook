# M8.7 Red Teaming - Files Guide (kaun si file kya karti hai, kaun kis ko import karti hai)

> Yahan class inheritance nahi, sirf `from x import y` wala import hai.
> **Dhyaan:** yeh module M8.9 ke secure agent ko import karta hai, is liye M8.9 pehle samjhein.

---

## 1. Import ka naqsha

```
 app/agent.py            (build_agent, run_turn, tool_calls, message_text)  -> INSECURE
 app/config.py           (OUTPUT_DIR)
 app/knowledge_base.py   (build_index, DOCS_DIR)
 m8_2/attacks.py         (ATTACKS)                                           -> attacks ki list
 m8_9/secure_agent.py    (build_secure_agent, secure_turn)                   -> SECURE
          |
          v
   attack_suite.py     (dono agents par saare attacks -> ASR -> report)


 m8_9/secure_agent.py  +  app/agent.py (message_text)
          |
          v
   deepteam_redteam.py (DeepTeam khud attacks banata hai, optional)
```

---

## 2. Parhne ka order

| # | File | Kyun |
|---|------|------|
| 0 | `m8_2/attacks.py`, `m8_9/secure_agent.py` | yeh dono pehle samajh aane chahiye |
| 1 | `attack_suite.py` | apna harness, koi extra install nahi |
| 2 | `deepteam_redteam.py` | optional, DeepTeam library |

---

## 3. Har file ka kaam

### `attack_suite.py`
| Kahan se | Kya liya |
|----------|----------|
| `app.agent` | `build_agent`, `tool_calls`, `message_text`, `run_turn` |
| `app.config` | `OUTPUT_DIR` |
| `app.knowledge_base` | `build_index`, `DOCS_DIR` |
| `m8_2_prompt_injection.attacks` | `ATTACKS` |
| `m8_9_capstone.secure_agent` | `build_secure_agent`, `secure_turn` |

- `REPORT` -> `outputs/redteam_report.json`
- `_run_insecure(agent, turns)` -> insecure agent par har turn, tool calls + aakhri jawab
- `_run_secure(agent, turns, use_model_guard)` -> secure agent par wahi. Block ho to history nahi badalti
- `evaluate(target, use_model_guard)` -> har attack chalao (S5 ke liye zehreela doc likh kar index
  dobara banao), `atk.succeeded()` se HIT / ok, aur
  **ASR = kamyab attacks / total attacks**
- `main()` -> insecure aur secure dono `evaluate`, table print, report save

### `deepteam_redteam.py`
- `model_callback(user_input)` -> DeepTeam ka sawal secure agent ko deta hai (`use_model_guard=False`)
- `main()` -> `red_team(...)` with `PromptLeakage`, `PIILeakage` vulnerabilities + `PromptInjection` attack.
  Attacker / judge Ollama par (`deepeval set-ollama`). `deepteam` na ho to sirf message

### `__init__.py`
Khaali. Folder ko package banata hai.

---

## 4. Chalana aur andar kya hota hai

```powershell
python -m m8_7_red_teaming.attack_suite --no-model-guard     # tez
python -m m8_7_red_teaming.attack_suite                      # Ollama moderation ke saath

# optional
pip install deepteam
deepeval set-ollama --model gpt-oss:20b-cloud
python -m m8_7_red_teaming.deepteam_redteam
```

```
attack_suite.main()
   |
   |-- evaluate("insecure")
   |      har attack: build_agent() -> _run_insecure() -> atk.succeeded() -> HIT / ok
   |
   |-- evaluate("secure")
   |      har attack: build_secure_agent() -> _run_secure()
   |                    -> secure_turn()  (guards + authz + RAG filter + log)
   |                  -> atk.succeeded() -> HIT / ok
   |
   '-- table:  attack | insecure | secure      +  ASR row
       report: outputs/redteam_report.json
```

---

## 5. Aage kahan kaam aati hain

Koi file isay import nahi karti. Yeh aakhri "naapne" wala step hai.
Jo attack secure par HIT ho, us ka permanent test `tests/security/` mein banta hai.

---

## 6. Yaad rakhne ki baat

- **S1 aur S2 secure agent par bhi HIT dikha sakte hain, chahe defence kaam kar rahi ho.**
  `attacks.py` ka check sirf yeh dekhta hai ke `get_order("ORD-2001")` ya `issue_refund(50000)`
  **call** hua. Secure agent ne call ko mana kar diya (`No order found` / approval queue),
  lekin check phir bhi HIT gin leta hai. Asli nuqsan dekhne ke liye tool ka **result** check hona chahiye.
- Bohat se model calls hote hain. Groq rate limit aaye to `.env` mein `LLM_PROVIDER=ollama`.
- S5 ke liye index poora mita kar dobara banta hai. Windows par yahan "PermissionError" /
  "readonly database" aa sakta hai (Chroma file band nahi hoti).
