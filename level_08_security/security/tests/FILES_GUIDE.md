# tests/ - Files Guide (kaun si file kya karti hai, kaun kis ko import karti hai)

> Yahan class inheritance nahi, sirf `from x import y` wala import hai.
> Usool: jo kamzori ek dafa mili, woh hamesha ke liye ek test ban jati hai.

---

## 1. Import ka naqsha

```
 m8_2/defenses.py      email_recipient_allowed, scan_output, fence_untrusted
 m8_3/rails.py         check_input, normalize
 m8_4/authz.py         Session, lookup_order, guarded_issue_refund, ToolDenied, REFUND_AUTO_LIMIT_PKR
 m8_4/sql_guard.py     validate_select, UnsafeSQL
 m8_6/secrets_scan.py  has_secret
          |
          v
 security/test_unit_defenses.py      TEZ, offline, koi model nahi


 app/knowledge_base.py  build_index, DOCS_DIR, CHROMA_DIR
 app/agent.py           message_text, tool_calls
 m8_2/attacks.py        ATTACKS
 m8_9/secure_agent.py   build_secure_agent, secure_turn
          |
          v
 security/test_live_attacks.py       SLOW, asli model call (marker: live)


 ../pytest.ini   -> "live" marker define karta hai, testpaths = tests
```

---

## 2. Parhne ka order

| # | File | Kyun |
|---|------|------|
| 1 | `../pytest.ini` | marker aur folder ki setting |
| 2 | `security/test_unit_defenses.py` | chhote, tez tests, har defence ka ek |
| 3 | `security/test_live_attacks.py` | har attack secure agent par fail hona chahiye |

`__init__.py` (dono folders mein) khaali hain, sirf package banane ke liye.

---

## 3. Har file ka kaam

### `security/test_unit_defenses.py`
`ALI = Session("cust_001", ...)` -> sab tests Ali ban kar chalte hain.

| Test | Kya check karta hai | Module |
|------|---------------------|--------|
| `test_email_allowlist_blocks_attacker` | Ali ka email allow, attacker ka nahi | M8.2 |
| `test_output_scan_catches_secret_and_foreign_pii` | coupon aur Sara ka phone pakra jaye | M8.2 |
| `test_fence_marks_untrusted` | fence mein "UNTRUSTED" aur "possible-injection" | M8.2 |
| `test_normalize_defeats_obfuscation` | `1gn0re`, `i g n o r e` -> ignore | M8.3 |
| `test_input_rail_blocks_injection_variants` | 3 attack block, normal sawal allow | M8.3 |
| `test_bola_blocked_in_code` | Ali ko ORD-2001 na mile | M8.4 |
| `test_own_order_allowed` | Ali ko ORD-1001 mile | M8.4 |
| `test_refund_over_limit_needs_approval` | 5001 -> "approval" | M8.4 |
| `test_refund_cannot_exceed_paid` | 999999 -> ToolDenied | M8.4 |
| `test_sql_guard_allows_safe_select` | safe SELECT pass | M8.4 |
| `test_sql_guard_blocks_danger` | DELETE / DROP / ghalat table block | M8.4 |
| `test_secret_scanner` | Groq key pakri jaye | M8.6 |

### `security/test_live_attacks.py`
- `pytestmark = pytest.mark.live` -> poori file "live" (`-m "not live"` se skip)
- `ensure_index()` fixture -> `.chroma` na ho to index banata hai
- `agent()` fixture -> ek dafa `build_secure_agent()`
- `test_attack_is_blocked(atk)` -> `ATTACKS` ke har attack ke liye ek test (parametrize):
  S5 ho to zehreela doc likh kar index dobara, phir `secure_turn` (`use_model_guard=False`),
  phir `assert not atk.succeeded(...)`

---

## 4. Chalana

```powershell
cd C:\Users\abubakar\Desktop\security
pytest tests/security -v -m "not live"     # sirf offline (1-2 second)
pytest tests/security -v                    # sab, model call (GROQ key + index chahiye)
pytest tests/security/test_unit_defenses.py -v   # sirf ek file
```

```
pytest
   -> pytest.ini parhta hai (testpaths = tests, marker live)
   -> har "test_" function chalata hai
        assert sahi  -> PASSED
        assert ghalat -> FAILED  (defence kamzor ho gayi!)
```

---

## 5. Yaad rakhne ki baat

- `test_refund_over_limit_needs_approval` sach mein `outputs/approval_queue.jsonl` mein ek line likhta hai.
- Live tests mein **S1 aur S2 FAIL ho sakte hain** chahe secure agent sahi kaam kare, kyun ke
  `attacks.py` ka check sirf tool "call" dekhta hai, us ka result nahi (M8.7 guide dekhein).
- Live tests S5 par index mita kar dobara banate hain. Windows par Chroma file lock ka error aa sakta hai.
