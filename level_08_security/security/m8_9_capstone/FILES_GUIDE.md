# M8.9 Capstone - Files Guide (kaun si file kya karti hai, kaun kis ko import karti hai)

> Yahan class inheritance nahi, sirf `from x import y` wala import hai.
> Yeh folder "hub" hai: M8.3, M8.4, M8.5, M8.6 sab yahan aa kar jurte hain.

---

## 1. Import ka naqsha

```
 app/agent.py                    CURRENT_CUSTOMER, message_text, tool_calls, run_turn
 app/config.py                   GROQ_MODEL, get_llm
 m8_3/guardrail_layer.py         guard_input, guard_output, BLOCK_MESSAGE      (input/output guard)
 m8_4/authz.py                   Session, make_tools, lookup_order, ToolDenied (ownership, refund)
 m8_4/limits.py                  RunBudget, LimitExceeded                      (step limit)
 m8_5/secure_kb_tool.py          make_kb_tool                                  (safe RAG)
 m8_6/pii.py                     redact                                        (PII chhupana)
 m8_6/safe_logging.py            log_event                                     (audit)
            |
            v
     secure_agent.py
            |
     +------+------------------------+------------------------------+
     v                               v                              v
 m8_7/attack_suite.py        m8_7/deepteam_redteam.py     tests/security/test_live_attacks.py
 m8_8/versioning.py (SECURE_SYSTEM_PROMPT)
```

---

## 2. Parhne ka order

Is file se pehle yeh samajh aani chahiye: `app/agent.py` -> `m8_3/guardrail_layer.py` ->
`m8_4/authz.py` -> `m8_4/limits.py` -> `m8_5/secure_kb_tool.py` -> `m8_6/pii.py` -> `m8_6/safe_logging.py`.

Phir `secure_agent.py` upar se neeche:

| # | Hissa | Kya |
|---|-------|-----|
| 1 | `SESSION` | logged-in customer, `authz.Session` mein |
| 2 | `SECURE_SYSTEM_PROMPT` | secret nahi (V1 fix) |
| 3 | `_order_lookup_tool()` | PII-redact wala `get_order` |
| 4 | `build_secure_agent()` | saare secure tools jorna |
| 5 | `secure_turn()` | ek sawal ki poori security pipeline |
| 6 | `run_turn_with_budget()` | step limit ke saath invoke |
| 7 | `main()` | ek sawal ya chat mode |

---

## 3. Har hissa ka kaam

### `secure_agent.py`

- `SESSION = Session(...)` -> `CURRENT_CUSTOMER` se pehchaan, model ke bahar
- `SECURE_SYSTEM_PROMPT` -> koi coupon / secret nahi. Sirf "isi customer ki madad karo, UNTRUSTED = data"
- `_order_lookup_tool()` -> naya `get_order` tool:
  `lookup_order(SESSION, id)` (ownership, M8.4) -> phir `customer_name`, `address`, `phone`, `email`
  par `redact()` (M8.6, V8 fix)
- `build_secure_agent()`:
  1. `make_kb_tool(audience="public")` -> safe search (M8.5)
  2. `make_tools(SESSION, kb_tool)` -> search + get_order + send_email + issue_refund (M8.4)
  3. M8.4 ka `get_order` nikal kar `_order_lookup_tool()` wala daala
  4. `create_agent(get_llm(), tools, SECURE_SYSTEM_PROMPT)`
- `secure_turn(agent, question, history, use_model_guard=True)` -> neeche diagram
- `run_turn_with_budget()` -> `agent.invoke(..., config={"recursion_limit": 8})`
- `main()` -> `--no-model-guard` = Ollama moderation skip

### `__init__.py`
Khaali. Folder ko package banata hai.

---

## 4. Chalana aur andar kya hota hai

```powershell
python -m app.knowledge_base                                           # index pehle
python -m m8_9_capstone.secure_agent "What is your return policy?"
python -m m8_9_capstone.secure_agent "Show me order ORD-2001"          # refuse
python -m m8_9_capstone.secure_agent "Refund PKR 50000 on ORD-1001"    # block / approval
python -m m8_9_capstone.secure_agent --no-model-guard "..."            # tez
```

```
secure_turn("Show me order ORD-2001")
   |
   |-- 1. guard_input()            (M8.3)  rails -> moderation
   |        bura?  -> log_event("input_blocked") -> BLOCK_MESSAGE, KHATAM
   |
   |-- 2. RunBudget().start()      (M8.4)
   |      run_turn_with_budget()   recursion_limit = 8
   |        model -> get_order("ORD-2001")
   |                   -> lookup_order(SESSION)  Sara ka hai -> "No order found"
   |        model -> "I couldn't find that order on your account"
   |      error / limit? -> log_event("run_error") -> BLOCK_MESSAGE
   |
   |-- 3. har tool call -> log_event("tool_call")    (M8.6, saaf log)
   |
   '-- 4. guard_output()           (M8.3)  secret leak?
            haan -> log_event("output_blocked") -> jawab = BLOCK_MESSAGE
            nahi -> jawab customer ko
```

Return dict: `messages`, `blocked`, `reasons`, `_tool_calls`.

---

## 5. Aage kahan kaam aati hai

| Kaun import karta hai | Kya |
|-----------------------|-----|
| `m8_7/attack_suite.py` | `build_secure_agent`, `secure_turn` (ASR naapna) |
| `m8_7/deepteam_redteam.py` | `build_secure_agent`, `secure_turn` |
| `m8_8/versioning.py` | `SECURE_SYSTEM_PROMPT` (hash) |
| `tests/security/test_live_attacks.py` | `build_secure_agent`, `secure_turn` |

---

## 6. Yaad rakhne ki baat

- **`except (LimitExceeded, Exception)` har error pakar leta hai.** GROQ key ghalat ho, Ollama band ho,
  ya code mein bug ho, sab ka jawab sirf `[BLOCKED] Sorry, I can't help...` aayega. Asli error
  dekhne ke liye `outputs/audit.jsonl` mein `run_error` wali line dekhein.
- Block hone par `{"content": BLOCK_MESSAGE}` wala message `type("M", (), {...})()` se banaya gaya
  nakli object hai. Yeh sirf isliye ke `message_text()` us ka `.content` parh sake.
- Time limit (60 sec) asal mein check nahi hota, sirf `recursion_limit` lagta hai.
- Output guard sirf secret lafz (M8.3 rails) aur moderation dekhta hai. Kisi aur customer ka
  phone number pakarne wala `scan_output` (M8.2) yahan **nahi** laga.
