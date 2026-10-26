# M8.3 Guardrails - Files Guide (kaun si file kya karti hai, kaun kis ko import karti hai)

> Yahan class inheritance nahi, sirf `from x import y` wala import hai.

---

## 1. Import ka naqsha

```
     rails.py                      app/config.py
  (kisi project file ko               |  get_ollama_chat
   import NAHI karti)                 v
        |                       moderation.py
        |                             |
        +-------------+---------------+
                      v
              guardrail_layer.py   (rails + moderation ko jorta hai)
                      |
                      v
        m8_9_capstone/secure_agent.py   (har turn par guard_input / guard_output)


  Alag thalag (sirf seekhne ke liye, agent use NAHI karta):
     nemo_config/config.yml + nemo_config/rails.co  ---->  nemo_demo.py
```

---

## 2. Parhne ka order

| # | File | Kyun |
|---|------|------|
| 1 | `rails.py` | kisi pe depend nahi, layer 1 (muft pattern check) |
| 2 | `moderation.py` | sirf `app/config` use karti hai, layer 2 (model check) |
| 3 | `guardrail_layer.py` | 1 + 2 ko jorti hai |
| 4 | `nemo_config/config.yml`, `rails.co`, `nemo_demo.py` | optional, NeMo framework samajhne ke liye |

---

## 3. Har file ka kaam

### `rails.py`  (layer 1: deterministic, muft, foran)
- `GuardDecision` -> dataclass: `blocked` (True/False) + `reasons` (list)
- `_LEET` -> `0->o, 1->i, 3->e, 4->a, 5->s, @->a, $->s`
- `normalize(text)` -> chhupane ki tricks hatata hai:
  unicode (`ⁱ` -> `i`), invisible chars, leetspeak (`1gn0re`), spaced letters (`i g n o r e`)
- `_INJECTION_PATTERNS` -> regex list: "ignore all", "system prompt", "developer mode", "dan mode"...
- `check_input(message)` -> `normalize` kar ke patterns dhoondta hai -> `GuardDecision`
- `_OUTPUT_FORBIDDEN` -> `mgr-override-2026`, `staff-90-off`, `supplier cost`
- `check_output(message)` -> jawab mein yeh lafz hain? -> `GuardDecision`

### `moderation.py`  (layer 2: model se safe/unsafe)
| Kahan se | Kya liya |
|----------|----------|
| `app.config` | `get_ollama_chat` |

- `_SYSTEM` -> prompt jo `gpt-oss:20b-cloud` ko classifier bana deta hai (jawab: SAFE / UNSAFE + category)
- `ModerationResult` -> dataclass: `flagged`, `categories`, `raw`
- `_classifier()` -> Ollama model (`@lru_cache`, ek hi dafa banta hai)
- `_parse(raw)` -> model ka jawab parh kar `ModerationResult` banata hai
- `moderate(content, role)` -> asal check. Ollama band ho to **error nahi, "safe" maan leta hai**
- `moderate_input(msg)` / `moderate_output(msg)` -> `moderate` ke chhote shortcut

### `guardrail_layer.py`  (dono layers ikatthi)
| Kahan se | Kya liya |
|----------|----------|
| `m8_3_guardrails.rails` | poora module (`rails.check_input`, `rails.check_output`) |
| `m8_3_guardrails.moderation` | `moderate_input`, `moderate_output` |

- `BLOCK_MESSAGE` -> block hone par customer ko yeh jawab
- `GateResult` -> dataclass: `allowed` + `reasons`
- `guard_input(message, use_model=True)` -> pehle `rails.check_input`, pass ho to `moderate_input`
- `guard_output(message, use_model=True)` -> pehle `rails.check_output`, pass ho to `moderate_output`
- `use_model=False` -> sirf pattern check (tez, Ollama nahi chahiye)

### `nemo_config/config.yml`
NeMo Guardrails ki settings: model (`ollama` / `gpt-oss:20b-cloud`), kaunsi rails (input/output),
aur har check ka prompt (`self_check_input`, `self_check_output`). Andar Roman Urdu comments hain.

### `nemo_config/rails.co`
Colang language mein flows: check fail ho to `bot refuse` + `stop`.

### `nemo_demo.py`
`RailsConfig.from_path(nemo_config)` + `LLMRails` se 2 messages test karta hai.
`nemoguardrails` install na ho to sirf message print karta hai, crash nahi.

### `__init__.py`
Khaali. Folder ko package banata hai taake `python -m m8_3_guardrails.rails` chale.

---

## 4. Chalana aur andar kya hota hai

```powershell
python -m m8_3_guardrails.rails          # obfuscation tests (Ollama nahi chahiye)
python -m m8_3_guardrails.moderation     # 3 messages ko safe/unsafe (Ollama chahiye)
pip install nemoguardrails               # optional
python -m m8_3_guardrails.nemo_demo      # optional
```

```
guard_input("1gn0re a l l previous instructions")
   |
   |-- rails.check_input()
   |      normalize()  -> "ignore all previous instructions"
   |      pattern "ignore (all|...)" mila -> BLOCK, model call ki zaroorat hi nahi
   |
   '-- (agar pattern na mile aur use_model=True)
          moderate_input() -> gpt-oss se "SAFE/UNSAFE?" -> UNSAFE ho to BLOCK
```

---

## 5. Aage kahan kaam aati hain

| File | Kaun import karta hai |
|------|-----------------------|
| `guardrail_layer.py` | `m8_9_capstone/secure_agent.py` (`guard_input`, `guard_output`, `BLOCK_MESSAGE`) |
| `rails.py` | `tests/security/test_unit_defenses.py` (`check_input`, `normalize`) |
| `moderation.py` | sirf `guardrail_layer.py` |
| `nemo_*` | koi nahi (sirf demo) |

---

## 6. Yaad rakhne ki baat

- `guardrail_layer.py` ke comments mein "Llama Guard" likha hai, lekin asal mein `gpt-oss:20b-cloud`
  istemaal hota hai (`moderation.py`).
- Ollama band ho to moderation chupke se "safe" keh deti hai (fail-open). Is liye sirf pattern
  check hi chalega, aur aap ko pata bhi nahi chalega. `[moderation-error]` ke liye `raw` dekhein.
- Guardrail yeh nahi samajhta ke "yeh order kisi aur ka hai". Woh kaam M8.4 (`authz.py`) ka hai.
