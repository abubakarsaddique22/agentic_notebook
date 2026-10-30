# PART A: 📦 Modules & Packages

## A.1 Module kya hai?
**Module = ek `.py` file.** Bas itna hi. Har `.py` file ko doosri file `import` kar sakti hai.

## A.2 Package kya hai?
**Package = folder jis mein modules hon**, aur aam taur par ek `__init__.py` file bhi.

```
bot/               ← package
├── __init__.py    ← "ye folder package hai" + package ka public interface
├── config.py      ← module
└── models.py      ← module
```

## A.3 Kyun zaroori hai?
| Ek hi `main.py` mein sab kuch | Modules mein baanta hua |
|---|---|
| 1500 lines, kuch dhoondna mushkil | Har file ka ek kaam |
| Test likhna mushkil | Har module alag test hota hai |
| Do log ek saath kaam karein to conflict | Har koi alag file par kaam kare |
| Code dobara use nahi hota | `from bot.tools import ...` kahin bhi |

## A.4 Hamara project structure
Ye wahi structure hai jo asli AI projects mein milta hai:

```
02_modules_pytest_debugging/
├── pyproject.toml        ← project + pytest settings
├── bot/                  ← main package (asli code)
│   ├── __init__.py
│   ├── config.py         ← settings (frozen dataclass)
│   ├── models.py         ← Message, Conversation
│   ├── llm.py            ← LLM API call (yahan fake, 2 sec)
│   ├── tools.py          ← order status tool
│   ├── pricing.py        ← bill calculate (is mein ek BUG hai 🐞)
│   └── main.py           ← sab ko jorta hai
├── tests/                ← saare tests
│   ├── conftest.py       ← shared fixtures
│   └── test_*.py
├── scripts/              ← demo scripts (crash, logging, pdb...)
├── circular_demo/        ← circular import ka demo
└── exercises/            ← exercises + solutions
```

**Golden rule:** Har module ka **ek** kaam ho. Config wali file mein LLM call nahi, tools wali file mein prompt nahi.

▶ `bot/` ki saari files kholein aur parhein. Har file ke upar docstring hai.

## A.5 `__init__.py`: package ka darwaza
`__init__.py` tab chalti hai jab koi `import bot` kare. Is ke teen kaam hain:
1. Batana ke **ye folder package hai** (Python 3.3+ mein bina is ke bhi chal jata hai, lekin hamesha rakhein: tools aur pytest ko clear signal milta hai)
2. **Shortcut imports:** user `from bot import Conversation` likh sake, `from bot.models import Conversation` ki jagah
3. Package level cheezein jaise `__version__`

`bot/__init__.py` mein **relative import** (`from .models`) hai. `.` ka matlab hai "isi package ke andar se".

## A.6 Import karne ke tareeqe

| Tareeqa | Misal | Kab |
|---|---|---|
| Specific cheez | `from bot.models import Conversation` | **Sab se common.** Saaf pata hai kya aa raha hai |
| Poora module | `from bot import tools` → `tools.get_order_status()` | Jab module ke kai functions chahiye hon aur naam saaf rakhne hon |
| Alias | `import numpy as np` | Lambe naam chhote karne ke liye |
| Package shortcut | `from bot import Conversation` | Jab `__init__.py` ne export kiya ho |
| Relative | `from .models import Message` | **Sirf package ke andar**, jaise `__init__.py` mein |
| ❌ Star | `from bot.models import *` | **Na karein.** Pata nahi chalta kya kahan se aaya |

**`sys.path`** = wo folders ki list jahan Python modules dhoondta hai. `python -m` chalane par current folder (project root) is list mein sab se pehle aata hai, is liye `import bot` kaam karta hai.

▶ `python -m scripts.a6_import_styles`

> **VS Code / Jupyter tip:** Agar aap kisi module ko badlein aur Jupyter mein use kar rahe hon, to notebook purana version hi use karti rahe gi, kyun ke Python module ko ek hi baar load karta hai. `importlib.reload(module)` karein, kernel restart karein, ya shuru mein `%load_ext autoreload` + `%autoreload 2`. Command line se `python -m` chalane par ye masla nahi hota, har run naya hota hai.

## A.7 `__name__` aur `if __name__ == "__main__":`

Har module ke paas ek variable `__name__` hota hai:
- File **import** hui → `__name__` = module ka naam (jaise `"bot.main"`)
- File **directly chalayi** gayi → `__name__` = `"__main__"`

Is liye `if __name__ == "__main__":` ke andar ka code **import karne par nahi chalta**. `a6_import_styles.py` mein dekhein: humne `bot.main` import kiya lekin us ka demo loop nahi chala.

## A.8 Package ko chalana: `python -m` ✅ vs file path ❌

Ye **sab se common** error hai jo naye log karte hain. Dono project root se try karein:

```
python bot\main.py        ← ❌ ModuleNotFoundError: No module named 'bot'
python -m bot.main        ← ✅ chalta hai
```

**Kyun fail hua?** `python bot\main.py` chalane par Python `sys.path` mein `bot\` folder daalta hai, project root nahi. Phir `import bot` dhoondne par `bot\` ke **andar** `bot` folder nahi milta, to `ModuleNotFoundError` aata hai.

**Hal:** project root se `python -m bot.main` chalayein (dots, `.py` nahi). Is se root `sys.path` mein jaati hai aur imports theek chalte hain.

## A.9 Circular import: do modules ek doosre ko import karein

`a.py` → `b.py` ko import kare, aur `b.py` → `a.py` ko. Python adhoora module load karta hai aur error deta hai.

```
cd circular_demo
python a.py
cd ..
```

Traceback mein dekhein: `a.py → b.py → a.py` ek **daira (circle)** ban gaya, aur aakhir mein `ImportError: cannot import name ...` aaya. Python ke version ke hisaab se message mein `partially initialized module` bhi likha ho sakta hai. Dono ka matlab circular import hai.

**Hal (aam taur par):**
1. Jo cheez dono ko chahiye, usay **teesre module** mein le jayein (jaise `common.py`)
2. Modules ki zimmedari dobara sochein. Circular import aksar is baat ka ishara hai ke design ulta hai
3. Aakhri hal: import ko function ke **andar** le jayein (lazy import)

Hamare project mein dekhein: `main` sab ko import karta hai, lekin koi bhi module `main` ko import nahi karta. Imports **ek taraf** behte hain: `main → tools/llm → config/models`.

## A.10 Common import errors: jaldi hal

| Error | Wajah | Hal |
|---|---|---|
| `ModuleNotFoundError: No module named 'bot'` | Ghalat folder se chalaya, ya `python file.py` use kiya | Project root se `python -m bot.main` |
| `ModuleNotFoundError: No module named 'pydantic'` | Library install nahi, ya **doosre** virtual env mein hai | `pip install ...` usi env mein jo active hai |
| `ImportError: attempted relative import with no known parent package` | Relative import (`from .x`) wali file ko directly chalaya | `python -m package.module` |
| `ImportError: cannot import name 'X'` aur traceback mein files ka daira (a → b → a) | Circular import | Upar A.9 dekhein |
| `ImportError: cannot import name 'X' from 'module'` | Naam ghalat hai ya function exist nahi karta | Spelling check karein |
| Apni file ka naam `random.py`, `json.py`, `openai.py` | Python asli library ki jagah aap ki file import kar leta hai | **Apni files ko library wale naam kabhi na dein** |
