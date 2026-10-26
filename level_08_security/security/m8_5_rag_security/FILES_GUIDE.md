# M8.5 RAG Security - Files Guide (kaun si file kya karti hai, kaun kis ko import karti hai)

> Yahan class inheritance nahi, sirf `from x import y` wala import hai.

---

## 1. Import ka naqsha

```
   app/knowledge_base.py  (get_store)
            |
            v
   secure_retrieval.py          m8_2_prompt_injection/defenses.py  (fence_untrusted)
            |                                |
            +---------------+----------------+
                            v
                   secure_kb_tool.py     (dono ko jor kar ek @tool banata hai)
                            |
                            v
             m8_9_capstone/secure_agent.py   (make_kb_tool(audience="public"))
```

---

## 2. Parhne ka order

| # | File | Kyun |
|---|------|------|
| 1 | `app/knowledge_base.py` ka `search()` | pehle dekhein ke purana search audience ignore karta hai (V5) |
| 2 | `secure_retrieval.py` | asli fix: filter + poison scan + provenance |
| 3 | `secure_kb_tool.py` | usay agent ka tool banana |

---

## 3. Har file ka kaam

### `secure_retrieval.py`
| Kahan se | Kya liya |
|----------|----------|
| `app.knowledge_base` | `get_store` |

- `_POISON_SIGNS` -> regex list: "ignore all", "system instruction", "do not tell",
  tool ke naam (`send_email|issue_refund|get_order`), "you must"
- `RetrievedChunk` -> dataclass: `text`, `source`, `audience`, `poison_flags`
  - `is_suspicious` -> `poison_flags` khaali nahi to True
- `_scan_poison(text)` -> kaun se poison patterns mile
- `secure_search(query, audience="public", k=3)` ->
  1. Chroma query mein hi `filter={"audience": audience}` (internal chunks load hi nahi hote)
  2. har chunk ko `_scan_poison`
  3. `RetrievedChunk` list wapas (source + audience = **provenance**)
- `format_for_model(chunks)` -> model ke liye text: shakki chunk ki jagah
  `[BLOCKED: possible injected instructions]`, baaki `[source: ...]` ke saath

### `secure_kb_tool.py`
| Kahan se | Kya liya |
|----------|----------|
| `m8_2_prompt_injection.defenses` | `fence_untrusted` |
| `m8_5_rag_security.secure_retrieval` | `secure_search`, `format_for_model` |

- `make_kb_tool(audience="public")` -> ek `search_knowledge_base` tool banata hai jo:
  `secure_search` -> `format_for_model` -> `fence_untrusted` (UNTRUSTED dabba)
  `audience` andar band (closure), customer ko `"public"`, staff tool ko `"internal"`

### `__init__.py`
Khaali. Folder ko package banata hai.

---

## 4. Chalana aur andar kya hota hai

```powershell
python -m app.knowledge_base                  # pehle index (agar nahi bana)
python -m m8_5_rag_security.secure_retrieval
```
Dikhega: `audience="public"` par internal notes **nahi** aati, `"internal"` par aati hain.

```
model: search_knowledge_base("staff discount coupon")
   |
   v
secure_search(query, audience="public")
   -> Chroma: similarity_search(..., filter={"audience": "public"})
        internal_staff_notes.md  -> filter se bahar (aaya hi nahi)
   -> har chunk: _scan_poison()
   |
   v
format_for_model()   -> shakki chunk BLOCKED, baaki [source: ...] ke saath
   |
   v
fence_untrusted()    -> "BEGIN UNTRUSTED STORE DOCUMENTS ... END"
   |
   v
model ko milta hai
```

---

## 5. Aage kahan kaam aati hain

| File | Kaun import karta hai |
|------|-----------------------|
| `secure_kb_tool.py` | `m8_9_capstone/secure_agent.py` (`make_kb_tool`) |
| `secure_retrieval.py` | sirf `secure_kb_tool.py` |

---

## 6. Yaad rakhne ki baat

- Filter **query ke andar** hai (source par), baad mein nahi. Yahi sahi tareeqa hai: jo chunk
  aaya hi nahi, woh leak bhi nahi ho sakta.
- Poison scan sirf regex hai. Koi naye alfaaz mein hukm likhe to bach sakta hai. Is liye
  fence (M8.2) aur code checks (M8.4) bhi saath lage hain.
- Multi-tenant store mein `tenant_id` bhi isi `filter` mein add karna hota hai.
