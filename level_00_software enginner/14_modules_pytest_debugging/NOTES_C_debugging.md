# PART C: 🐞 Debugging

**Debugging** = bug ki **wajah** dhoondna. Teen main hathiyar hain:

| Hathiyar | Kab |
|---|---|
| **Stack trace** | Program crash hua → kya aur kahan hua |
| **Logging** | Program chal raha hai lekin ghalat kaam kar raha hai, ya production mein kya hua |
| **Breakpoints (debugger)** | Code ko rok kar har variable ki value andar se dekhna |

## C.1 Stack trace parhna

▶ `python -m scripts.crash_demo` (ye jaan boojh kar crash hoti hai)

### Kaise parhein: **neeche se upar** ⬆️

```
Traceback (most recent call last):          ← purani call upar, nayi neeche
  File "<frozen runpy>", ...                ← python -m ki apni lines, skip karein
  File "...\scripts\crash_demo.py", line 17, in <module>
    print(reply_for("Salam"))               ← 3. yahan se shuru hua
  File "...\scripts\crash_demo.py", line 14, in reply_for
    return get_order_status(order_id)       ← 2. ASAL GHALTI: None pass kiya
  File "...\bot\tools.py", line 32, in get_order_status
    order_id = order_id.strip()             ← 1. crash yahan hua
AttributeError: 'NoneType' object has no attribute 'strip'
                                            ← 0. KYA hua (pehle ye parhein)
```

**3 qadam:**
1. **Aakhri line:** error ki **kism** aur message. `'NoneType' ... no attribute 'strip'` ka matlab hai koi variable `None` tha
2. **Us se upar wali `File` line:** **kahan** crash hua (`tools.py`, line 32)
3. **Aur upar jayein** jab tak wajah na mile. Crash `tools.py` mein hua, lekin **ghalti** `crash_demo.py` mein hai jahan `None` check nahi kiya

> **Tips:**
> - `site-packages` aur `<frozen ...>` wali lines library/Python ki hain. Unhein skip kar ke **apni file** dhoondein
> - `'NoneType' object has no attribute ...` sab se common Python error hai. mypy ise **chalaye baghair** pakar leta (`extract_order_id` ka return type `str | None` hai)
> - Kabhi do tracebacks hote hain, beech mein *"During handling of the above exception, another exception occurred"*. Pehla wala asal wajah hota hai

### Common errors ka matlab
| Error | Aam wajah |
|---|---|
| `AttributeError: 'NoneType'...` | Function ne `None` lautaya, aap ne check nahi kiya |
| `KeyError: 'text'` | Dict mein woh key nahi (LLM/API response ka format alag tha) |
| `IndexError: list index out of range` | Khali list par `[0]` |
| `TypeError: ... got an unexpected keyword argument` | Function ka argument naam ghalat |
| `TypeError: unsupported operand ... 'str' and 'int'` | Number string ki shakal mein aaya (JSON/input se) |
| `ValueError` | Type sahi lekin value ghalat (`int("abc")`) |

### Traceback bina crash ke dekhna
`try/except` ke saath `traceback.print_exc()` se poora traceback print hota hai lekin program nahi rukta. Production mein yahi kaam `logger.exception()` karta hai (C.2).

▶ `python -m scripts.traceback_demo`

## C.2 `print` ki jagah `logging`

| `print()` | `logging` |
|---|---|
| Har jagah se hatana parta hai | Level badlo, bas. Code mein reh sakta hai |
| Time, file ka naam nahi | Time, module ka naam, level khud aata hai |
| Sab kuch ek jaisa | DEBUG / INFO / WARNING / ERROR / CRITICAL |
| Sirf screen par | Screen, file, ya cloud (production) |

### Levels: kab kaunsa
| Level | Kab | Misal |
|---|---|---|
| `DEBUG` | Detail sirf development ke liye | Poora prompt, API ka raw response |
| `INFO` | Normal kaam ho raha hai | "Naya message aaya", "LLM call: 230 tokens" |
| `WARNING` | Kuch ajeeb, lekin chal raha hai | "Order nahi mila", "retry kar rahe hain" |
| `ERROR` | Kaam fail hua | "LLM call fail", "Shopify API down" |
| `CRITICAL` | Poora system khatre mein | "Database connect nahi ho raha" |

### Pattern jo har project mein use hota hai
- **Har module mein:** `logger = logging.getLogger(__name__)` (hamari `tools.py`, `llm.py`, `main.py` mein yahi hai)
- **Sirf entry point** (`main.py` ka `__main__` block) mein `logging.basicConfig(...)` ek baar

▶ `python -m scripts.logging_demo` (levels, level badalna, `bot.log` file mein save)

### 🔐 AI projects mein logging ke rules
- ✅ Log karein: model ka naam, token count, latency, tool ka naam, kaunsa step fail hua
- ✅ `%s` style use karein: `log.info("x=%s", x)`. f-string ki jagah ye behtar hai, kyun ke agar level band ho to string banti hi nahi
- ❌ **API keys, access tokens** kabhi log na karein
- ❌ Customer ka poora phone/address/personal data na likhein. Zaroorat ho to mask karein (`9230****567`)
- ❌ Har jagah DEBUG mein poora prompt production mein na chhorein (bohat bari files aur privacy masla)

## C.3 Breakpoints: code ko rok kar andar dekhna

### Tareeqa 1: VS Code debugger (sab se aasan, rozana yahi use karein)
1. Project folder VS Code mein kholein (`File → Open Folder` → `02_modules_pytest_debugging`)
2. `.py` file kholein, line number ke **left** par click karein. 🔴 laal dot lag jaye ga (ya `F9`)
3. `F5` dabayein → "Python Debugger" → "Python File" chunein
4. Code laal dot wali line par **ruk** jaye ga
5. Left panel **VARIABLES** mein har variable ki value nazar aaye gi
6. Controls:

| Key | Kaam |
|---|---|
| `F5` | Aage chalao (agle breakpoint tak) |
| `F10` | **Step Over:** agli line (function ke andar mat jao) |
| `F11` | **Step Into:** function ke andar jao |
| `Shift+F11` | **Step Out:** function se bahar aao |
| `Shift+F5` | Debugging band |

> ⚠️ Is project ki files `from bot...` import karti hain. VS Code ka "Python File" mode bhi `python bot\main.py` jaisa chalata hai aur A.8 wala error aa sakta hai. Behtar: `F5` → "Python Debugger" → **"Module"** chunein aur `bot.main` likhein. Ya **Testing** tab (beaker 🧪) se test ko "Debug Test" karein.

**Pro tips:**
- 🔴 par right click → **Conditional Breakpoint** → `order_id is None`. Ab sirf tab rukay ga jab condition sach ho (loop mein bohat kaam aata hai)
- **DEBUG CONSOLE** mein ruke hue program par koi bhi Python likh kar chala sakte hain

### Tareeqa 2: `breakpoint()` (koi bhi editor, terminal)
Code mein kahin bhi `breakpoint()` likh dein. Program wahan ruk kar `(Pdb)` prompt de ga:

| Command | Kaam |
|---|---|
| `n` | next line |
| `s` | step into function |
| `c` | continue |
| `p var` | variable ki value print |
| `pp var` | pretty print (dict/list ke liye) |
| `l` | aas paas ka code dikhao |
| `w` | stack trace: abhi kahan hoon |
| `q` | quit |

▶ `python -m scripts.breakpoint_demo` (interactive, `p price` likh kar try karein)

pytest ke saath: `python -m pytest --pdb` → test fail hote hi debugger khul jata hai.

### Tareeqa 3: Jupyter mein `%debug`
Kisi cell mein error aaye to **agle cell** mein sirf `%debug` likh kar chalayein. Crash wali jagah par debugger khul jaye ga (wahi `p`, `w`, `q` commands).

## C.4 🕵️ Bug Hunt: pricing ka bug pakarna

Part B mein `test_pricing.py` ke 3 tests fail hue the. Ab **professional tareeqe** se bug dhoondte hain.

### Debugging ka 5 qadam ka workflow
1. **Reproduce:** bug ko pakka dobara paida karein (hamare paas failing test hai ✅)
2. **Isolate:** sab se chhota case dhoondein jo fail ho
3. **Inspect:** values dekhein (print/log/breakpoint)
4. **Fix:** wajah theek karein, symptom nahi
5. **Verify:** test dobara chalayein, aur baqi tests bhi

### Qadam 1–2: sirf pricing tests
```
python -m pytest tests/test_pricing.py -q
```

### Qadam 3: Inspect
Clues:
- `0%` discount pass, lekin `10%` aur `20%` fail
- `apply_discount(1000, 10)` ne `-9000` diya. 1000 se bhi **zyada** minus ho gaya

```
python -m scripts.inspect_pricing
```
Ya VS Code mein `bot/pricing.py` ki `return` line par breakpoint laga kar Testing tab se `test_apply_discount` ko "Debug Test" karein.

<details><summary>🎯 Wajah (pehle khud sochein, phir click karein)</summary>

`discount_percent` ki value **10** hai (yani 10%), lekin code isay **0.10** ki tarah use kar raha hai. `1000 * 10 = 10000` minus ho raha hai, jab ke `100` hona chahiye tha. Yani **100 se taqseem karna bhool gaye**.
</details>

### Qadam 4: Fix
**Pehle khud theek karein!** `bot/pricing.py` VS Code mein khol kar `apply_discount` ki return line theek karein. Saath mein validation bhi daalein: discount 0 se 100 ke beech na ho to `ValueError`.

Solution: `exercises/solutions/pricing_fixed.py`

### Qadam 5: Verify, **poora** test suite
Validation ka bhi test likhna chahiye, taake ye bug dobara na aaye. Is ko **regression test** kehte hain. `tests/test_pricing.py` ke aakhir mein jorein:

```python
@pytest.mark.parametrize("bad", [-5, 150])
def test_invalid_discount_raises(bad):
    with pytest.raises(ValueError):
        apply_discount(1000, bad)
```
Phir:
```
python -m pytest -q
```
Saare tests pass 🎉. Ab agar kabhi koi `/ 100` hata de ga, to test foran bata de ga.

**Sabaq:**
- Bug **test** ne pakra, customer ne nahi
- Sirf `0%` wala test hota to bug kabhi nazar na aata. **Kai inputs** (`parametrize`) zaroori hain
- Fix ke baad **poora** suite chalayein, sirf ek test nahi
