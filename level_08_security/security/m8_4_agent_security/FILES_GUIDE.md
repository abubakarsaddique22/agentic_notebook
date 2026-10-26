# M8.4 Agent Security - Files Guide (kaun si file kya karti hai, kaun kis ko import karti hai)

> Is module mein kuch **asli class inheritance** bhi hai: `ToolDenied(Exception)`,
> `LimitExceeded(Exception)`, `UnsafeSQL(Exception)`. Yani yeh apni banayi hui error types hain
> jo Python ki `Exception` se bani hain, taake `raise` / `except` ho sakein. Baaki sab import hai.

---

## 1. Import ka naqsha

```
   app/config.py  (DATA_DIR, OUTPUT_DIR)
   app/tools.py   (_append_jsonl, OUTBOX_FILE, REFUNDS_FILE)
          |
          v
       authz.py          limits.py          sql_guard.py        sandbox.py
          |            (koi project         (sirf sqlglot)      (koi project
          |             import nahi)                             import nahi)
          |                 |
          +--------+--------+
                   v
     m8_9_capstone/secure_agent.py   (authz + limits use karta hai)

   tests/security/test_unit_defenses.py  ->  authz.py, sql_guard.py
```

`sql_guard.py` aur `sandbox.py` agent mein **istemaal nahi hoti**. Yeh sirf dikhati hain ke
model ka banaya SQL / code bhi bina-bharose hai.

---

## 2. Parhne ka order

| # | File | Kyun |
|---|------|------|
| 1 | `authz.py` | is module ka dil: ownership, email allow-list, refund + approval |
| 2 | `limits.py` | chhoti file, step / time limit |
| 3 | `sql_guard.py` | optional idea: SQL ko check karna |
| 4 | `sandbox.py` | optional idea: code ko band container mein chalana |

---

## 3. Har file ka kaam

### `authz.py`  (S1, S2, S6 ka ASLI fix)
| Kahan se | Kya liya |
|----------|----------|
| `app.config` | `DATA_DIR`, `OUTPUT_DIR` |
| `app.tools` | `_append_jsonl`, `OUTBOX_FILE`, `REFUNDS_FILE` |

- `REFUND_AUTO_LIMIT_PKR = 5000` -> is se upar refund insaan approve karega
- `APPROVAL_QUEUE` -> `outputs/approval_queue.jsonl`
- `Session` -> dataclass: `customer_id`, `name`, `email` (pehchaan CODE deta hai, model nahi)
- `ToolDenied(Exception)` -> jab kaam mana ho
- `_load_orders()` -> orders.json parhna
- `owns_order(session, order)` -> kya order isi customer ka hai?
- `lookup_order(session, order_id)` -> order do, warna `ToolDenied`. Doosre ka order ho ya
  mojood hi na ho, **dono ka message ek jaisa** (attacker ko pata na chale order mojood hai)
- `guarded_send_email(session, to, ...)` -> `to` customer ka apna email na ho to `ToolDenied`
- `guarded_issue_refund(session, order_id, amount)` -> check: apna order? > 0? paid se kam?
  5000 se upar -> approval queue (refund nahi hota)
- `make_tools(session, search_tool)` -> upar wale functions ko `@tool` bana kar list deta hai.
  Andar **closure** hai: tools ke andar `session` "band" ho jata hai, model use badal nahi sakta.
  `search_tool` bahar se aata hai (M8.5 wala)

### `limits.py`  (V9 / S8)
- `MAX_STEPS = 8` -> agent ke steps ki hadd
- `WALL_CLOCK_SECONDS = 60` -> waqt ki hadd
- `LimitExceeded(Exception)` -> hadd paar hone par
- `RunBudget` -> dataclass:
  - `start()` -> timer shuru
  - `check_time()` -> 60 second paar? to `LimitExceeded`
  - `config` -> `{"recursion_limit": 8}` (agent.invoke ko diya jata hai)

### `sql_guard.py`
- `ALLOWED_TABLES = {"orders", "products"}`
- `BANNED` -> insert, update, delete, drop... lafzon ki list
- `UnsafeSQL(Exception)`
- `validate_select(sql)` -> sqlglot se parse: sirf 1 statement? SELECT hai? banned lafz nahi?
  sirf allowed tables? Sab theek to SQL wapas, warna `UnsafeSQL`

### `sandbox.py`
- `HARDENING` -> docker flags list (no network, read-only, memory/CPU cap, non-root...)
- `build_docker_command(code)` -> ek `docker run` command **banata aur print** karta hai, khud chalata nahi

### `__init__.py`
Khaali. Folder ko package banata hai.

---

## 4. Chalana aur andar kya hota hai

```powershell
python -m m8_4_agent_security.sql_guard      # 4 SQL ko ALLOW / DENY
python -m m8_4_agent_security.sandbox        # docker command print
```
`authz.py` aur `limits.py` ka apna `__main__` nahi. Yeh M8.9 secure agent ke andar chalti hain:

```
model: issue_refund("ORD-1001", 50000)      <- sirf REQUEST
   |
   v
make_tools ka issue_refund
   -> guarded_issue_refund(SESSION, "ORD-1001", 50000)
        -> lookup_order()  : Ali ka order hai? haan
        -> 50000 > 8750 paid?  haan -> ToolDenied("cannot exceed...")
   -> "BLOCKED: Refund cannot exceed what was paid"   <- model ko yeh milta hai
```

---

## 5. Aage kahan kaam aati hain

| File | Kaun import karta hai |
|------|-----------------------|
| `authz.py` | `m8_9/secure_agent.py` (`Session`, `make_tools`, `lookup_order`, `ToolDenied`), tests |
| `limits.py` | `m8_9/secure_agent.py` (`RunBudget`, `LimitExceeded`) |
| `sql_guard.py` | tests |
| `sandbox.py` | koi nahi |

---

## 6. Yaad rakhne ki baat

- **Time limit asal mein kaam nahi karta.** `RunBudget.check_time()` kahin call hi nahi hota
  (m8_9 sirf `budget.config` use karta hai). Sirf `recursion_limit = 8` waqai lagta hai.
- `sql_guard.py` ka `BANNED` check poore SQL text mein lafz dhoondta hai, is liye `created_at`
  jaisa column bhi "create" ki wajah se DENY ho jayega (false positive).
- Refund ke liye order ka "delivered" hona check nahi hota (returns policy kehti hai delivery ke baad).
- `test_refund_over_limit_needs_approval` chalne par `outputs/approval_queue.jsonl` mein sach mein
  ek line likhi jati hai.
