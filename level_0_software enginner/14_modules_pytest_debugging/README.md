# 📦 Modules & Packages · 🧪 pytest · 🐞 Debugging
### AI Engineer ke liye Practice Folder (Roman Urdu)

Ye folder **khud ek chhota project hai** (`practice_bot`), jo ek WhatsApp support bot jaisa hai. Notebook mein jo files `%%writefile` se banti thin, wo ab yahan pehle se maujood hain. Aap seedha cmd se chalayein ge.

## 📁 Structure

```
02_modules_pytest_debugging/
├── README.md               ← ye file
├── NOTES_A_modules.md      ← Theory: modules, packages, imports, python -m, circular import
├── NOTES_B_pytest.md       ← Theory: assert, fixtures, parametrize, raises, caplog, mocking
├── NOTES_C_debugging.md    ← Theory: stack trace, logging, breakpoints, bug hunt
├── CHEATSHEET.md           ← Sab kuch ek page par
├── pyproject.toml          ← project + pytest settings
├── bot/                    ← asli code (package)
│   ├── __init__.py  config.py  models.py  llm.py  tools.py  main.py
│   └── pricing.py          ← 🐞 is mein jaan boojh kar bug hai (Part C.4)
├── tests/                  ← pytest tests (conftest.py + test_*.py)
├── scripts/                ← demos: imports, crash, traceback, logging, breakpoint, inspect
├── circular_demo/          ← a.py ↔ b.py circular import
└── exercises/              ← EXERCISES.md + solutions/
```

## ⚙️ Setup (Windows, ek baar)
```
cd path\to\02_modules_pytest_debugging
python -m venv .venv
.venv\Scripts\activate
pip install pytest
```

> **Hamesha isi folder ki ROOT se commands chalayein**, aur `python -m` ke saath (dots, bina `.py`).

## ▶️ Parhne aur chalane ka order

### Part A: Modules & Packages → `NOTES_A_modules.md`
```
python -m bot.main                      ← bot chalao (A.4, A.7)
python bot\main.py                      ← ❌ ye fail hoga, kyun? (A.8)
python -m scripts.a6_import_styles      ← import ke tareeqe, __name__ (A.6, A.7)
```
Circular import (A.9), teen alag commands:
```
cd circular_demo
python a.py
cd ..
```

### Part B: pytest → `NOTES_B_pytest.md`
```
python -m pytest -v                     ← saare tests (shuru mein 3 fail, 21 pass)
python -m pytest tests\test_models.py -v
python -m pytest -k order -q
python -m pytest -x -q
```

### Part C: Debugging → `NOTES_C_debugging.md`
```
python -m scripts.crash_demo            ← stack trace parhna (C.1)
python -m scripts.traceback_demo        ← bina crash traceback (C.1)
python -m scripts.logging_demo          ← logging levels + bot.log file (C.2)
python -m scripts.breakpoint_demo       ← pdb, interactive (C.3)
python -m pytest tests\test_pricing.py -q   ← bug hunt shuru (C.4)
python -m scripts.inspect_pricing       ← bug hunt: values dekhna (C.4)
```
Phir `bot\pricing.py` **khud theek karein**, regression test jorein, aur `python -m pytest -q` se sab green karein.

### Part D: Exercises → `exercises\EXERCISES.md`
4 exercises: naya `bot/faq.py`, us ke tests, FAQ ko bot mein jorna (mocking ke saath), aur `crash_demo` theek karna.

### Part E: `CHEATSHEET.md`

## 🔄 Shuru se dobara practice karni ho?
Is folder ki ek copy pehle hi bana kar rakh lein (zip dobara extract kar lein). Kyun ke exercises mein aap `bot/` aur `tests/` ki files khud badlein ge.
