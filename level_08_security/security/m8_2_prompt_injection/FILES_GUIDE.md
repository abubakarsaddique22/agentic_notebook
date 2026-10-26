# M8.2 - Files Guide (kaun si file kya karti hai, kaun kis ko import karti hai)

> Note: yahan class wali "inheritance" nahi ho rahi. Files ek doosre se functions
> **import** karti hain (`from x import y`). Neeche wahi "kaun kis se leta hai" ka naqsha hai.

---

## 1. Ek nazar mein: import ka naqsha

```
                    app/config.py            (models + paths, kisi ko import nahi karta)
                         |
                         v
                 app/knowledge_base.py       (Chroma index: build_index, search)
                         |
                         v
                    app/tools.py             (4 INSECURE tools)
                         |
                         v
                    app/agent.py             (INSECURE agent + helpers)
                         |
        +----------------+-----------------+
        |                                  |
        v                                  v
  defended_agent.py  <---- defenses.py     |
        |                                  |
        +---------------+     attacks.py   |
                        |         |        |
                        v         v        v
                     run_attacks.py   <----+        <== YEHI FILE AAP CHALATE HAIN


  Alag thalag (run_attacks inhe istemaal NAHI karta):
     policies.py  ---->  secure_tools.py     (secure_tools.py TOOTI hui hai, neeche dekhein)
```

Teer (`-->`) ka matlab: "yeh file us file se cheezein leti hai".

---

## 2. Parhne ka sahi order

Is order mein parhein, har file sirf pichli files par depend karti hai:

| # | File | Kyun is number par |
|---|------|--------------------|
| 1 | `app/config.py` | sab se neeche ki file, kisi pe depend nahi |
| 2 | `app/knowledge_base.py` | config use karti hai |
| 3 | `app/tools.py` | knowledge_base + config use karti hai |
| 4 | `app/agent.py` | tools use karti hai |
| 5 | `m8_2/attacks.py` | kisi project file pe depend nahi, sirf attacks ki list |
| 6 | `m8_2/defenses.py` | kisi project file pe depend nahi, sirf defence functions |
| 7 | `m8_2/defended_agent.py` | app/ + defenses.py ko jorti hai |
| 8 | `m8_2/run_attacks.py` | sab ko jorti hai, **yahi chalti hai** |
| - | `m8_2/policies.py`, `m8_2/secure_tools.py` | is module mein istemaal nahi hoti, skip karein |

---

## 3. Har file ka kaam

### `app/config.py`
Saari settings ek jagah.
- `ROOT`, `DOCS_DIR`, `CHROMA_DIR`, `OUTPUT_DIR` -> folders ke paths
- `get_llm()` -> Groq (ya Ollama) model, **yahi model attack hota hai**
- `get_embeddings()` -> Ollama `all-minilm` (RAG ke liye)
- `get_ollama_chat()` -> moderation ke liye (M8.3 mein)

### `app/knowledge_base.py`
RAG ka index.
- `build_index()` -> `app/data/docs/*.md` parh kar Chroma mein daalta hai
- `search(query)` -> milte julte 3 chunks laata hai (**audience filter nahi**, V5)

### `app/tools.py`
4 INSECURE tools jo agent chala sakta hai:
- `search_knowledge_base` -> docs ka text seedha model ko (V6)
- `get_order` -> **kisi ka bhi** order (V2 BOLA)
- `send_email` -> **kisi bhi** address par (V3)
- `issue_refund` -> koi limit nahi (V4)
- helpers: `_append_jsonl()` (outputs/ mein likhna), `OUTBOX_FILE`, `REFUNDS_FILE`

### `app/agent.py`
INSECURE agent.
- `CURRENT_CUSTOMER` -> logged-in Ali Raza
- `SYSTEM_PROMPT` -> is mein secret coupon hai (V1)
- `build_agent()` -> agent banata hai
- `run_turn(agent, question, history)` -> ek sawal bhejta hai
- `tool_calls(result)` -> result se tool calls nikalta hai
- `message_text(message)` -> message ka text nikalta hai

---

### `m8_2/attacks.py`  (kisi project file ko import NAHI karti)
Attacks ki list, DATA ki tarah.
- `Attack` -> ek attack ka dhancha: `id`, `kind`, `turns`, `succeeded`, `poison_doc`
- `ATTACKS` -> 6 attacks: S1, S3, S2, S5, S6, S4
- `_called(calls, name, args)` -> kya yeh tool in arguments se call hua?
- `_text_has(text, ...)` -> kya jawab mein yeh lafz hai?
- `by_kind(kind)` -> sirf ek qisam ke attacks (direct / indirect / exfiltration)

### `m8_2/defenses.py`  (kisi project file ko import NAHI karti)
Defence ke simple functions (koi LLM nahi):
- `fence_untrusted(label, text)` -> text ko "UNTRUSTED DATA" ke dabbe mein band karta hai
- `LEAST_PRIVILEGE_RULES` -> prompt mein daalne wale security rules
- `email_recipient_allowed(to, customer_email)` -> email sirf customer ko
- `scan_output(text)` -> jawab mein secret / phone / email leak dhoondta hai
- `SAFE_REFUSAL` -> leak mile to yeh jawab

### `m8_2/defended_agent.py`
INSECURE agent ko defences ke saath lapet deta hai.

| Kahan se | Kya liya |
|----------|----------|
| `app.config` | `get_llm` |
| `app.knowledge_base` | `search` |
| `app.tools` | `get_order`, `issue_refund` (**waise hi purane**), `_append_jsonl`, `OUTBOX_FILE` |
| `app.agent` | `CURRENT_CUSTOMER`, `message_text`, `tool_calls`, `run_turn` |
| `defenses` | `LEAST_PRIVILEGE_RULES`, `SAFE_REFUSAL`, `email_recipient_allowed`, `fence_untrusted`, `scan_output` |

Banata kya hai:
- `DEFENDED_SYSTEM_PROMPT` -> secret nahi + security rules
- `search_knowledge_base_fenced` -> search + `fence_untrusted`
- `send_email_guarded` -> `email_recipient_allowed` check
- `DEFENDED_TOOLS` -> naye 2 + purane 2 tools
- `build_defended_agent()` -> defended agent
- `run_turn_defended()` -> `run_turn` + `scan_output` (leak ho to `SAFE_REFUSAL`)

### `m8_2/run_attacks.py`  <== YEH CHALATE HAIN
Sab ko jor kar attacks chalata hai.

| Kahan se | Kya liya |
|----------|----------|
| `app.agent` | `build_agent`, `run_turn`, `tool_calls`, `message_text` |
| `app.knowledge_base` | `build_index`, `DOCS_DIR` |
| `attacks` | `by_kind` |
| `defended_agent` | `build_defended_agent`, `run_turn_defended` |

Functions:
- `run_conversation(target, agent, turns)` -> attack ke saare turns chalata hai
- `write_poison()` / `remove_poison()` -> zehreela doc `app/data/docs/` mein likhna / mitana
- `main()` -> har attack chala kar SUCCESS / BLOCKED print karta hai

### `m8_2/policies.py`  (istemaal nahi hoti)
Refund aur ownership ke rules (`can_access_order`, `decide_refund`). Sirf `secure_tools.py`
isay import karti hai. Yahi idea M8.4 (`m8_4_agent_security/authz.py`) mein dobara likha gaya hai.

### `m8_2/secure_tools.py`  (TOOTI hui, istemaal nahi hoti)
Yeh `defenses.py` se `detect_injection` aur `validate_output` import karti hai, lekin yeh dono
functions `defenses.py` mein **mojood hi nahi**. Is file ko import karte hi `ImportError` aayega.
Koi aur file isay import nahi karti, is liye `run_attacks` par asar nahi. **Skip karein.**

### `m8_2/__init__.py`
Khaali file. Sirf Python ko batati hai ke yeh folder ek "package" hai, taake
`python -m m8_2_prompt_injection.run_attacks` kaam kare.

---

## 4. Jab aap chalate hain to andar kya hota hai

```powershell
python -m m8_2_prompt_injection.run_attacks --target insecure
python -m m8_2_prompt_injection.run_attacks --target defended
```

```
run_attacks.main()
   |
   |-- --target dekha:
   |      insecure -> build_agent()            (app/agent.py)
   |      defended -> build_defended_agent()   (defended_agent.py)
   |
   |-- by_kind() se attacks ki list li         (attacks.py)
   |
   '-- HAR attack ke liye:
         1. poison_doc hai? (sirf S5)
              -> write_poison()  file app/data/docs/ mein likhi
              -> build_index()   index dobara bana        (app/knowledge_base.py)
         2. agent = build_fn()   naya agent
         3. run_conversation()   har turn:
              insecure -> run_turn()            (app/agent.py)
              defended -> run_turn_defended()   (defended_agent.py)
                            = run_turn() + scan_output()   (defenses.py)
         4. atk.succeeded(calls, text)          (attacks.py ka check)
              True  -> "SUCCESS (bad)"
              False -> "BLOCKED (good)"
         5. poison_doc tha? -> remove_poison() + build_index() wapas saaf
   |
   '-- aakhir mein: "X/6 attacks succeeded"
```

---

## 5. M8.2 ki files aage kahan kaam aati hain

| M8.2 file | Aage kaun import karta hai |
|-----------|----------------------------|
| `defenses.py` (`fence_untrusted`) | `m8_5_rag_security/secure_kb_tool.py` |
| `defenses.py` (sab) | `tests/security/test_unit_defenses.py` |
| `attacks.py` (`ATTACKS`) | `m8_7_red_teaming/attack_suite.py`, `tests/security/test_live_attacks.py` |
| `defended_agent.py`, `run_attacks.py` | koi nahi (sirf M8.2 ka demo) |

---

## 6. Yaad rakhne ki baat

- `defended` ke baad bhi **S1** (Sara ka order) aur **S2** (bara refund) kamyab ho sakte hain,
  kyun ke `defended_agent.py` ne `get_order` aur `issue_refund` **purane** hi rakhe hain.
  Inka asli fix M8.4 (`authz.py`) mein hai.
- S1 aur S2 ka check sirf yeh dekhta hai ke tool **call** hua, yeh nahi ke kaam waqai hua.
  Is liye baad mein secure agent par bhi yeh "SUCCESS" dikha sakte hain, chahe tool ne mana kar diya ho.
