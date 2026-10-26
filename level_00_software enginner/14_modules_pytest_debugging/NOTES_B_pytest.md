# PART B: 🧪 Unit Tests (pytest)

## B.1 Test kya hai aur kyun?
**Test** ek chhota function hai jo aap ke code ko chalata hai aur check karta hai ke jawab **sahi** hai.

Kyun likhein?
- Kal ko code badla to **2 second** mein pata chal jaye ga ke kuch toota to nahi
- Bot ko har baar WhatsApp par message bhej kar manually check nahi karna parta
- Bug theek kiya to test us bug ko **wapas aane nahi deta**
- Job interviews aur client projects mein **tests wala code professional** lagta hai

## B.2 pytest ke rules
| Rule | Misal |
|---|---|
| Test file ka naam `test_` se shuru | `tests/test_models.py` |
| Test function ka naam `test_` se shuru | `def test_history_limit():` |
| Check karne ke liye sirf `assert` | `assert result == 5` |
| Shared fixtures `conftest.py` mein | pytest khud dhoond leta hai, import nahi karna parta |

## B.3 Commands (Windows cmd, project root se)
```
python -m pytest              # saare tests
python -m pytest -v           # har test ka naam aur result
python -m pytest -x           # pehla fail aate hi ruk jao
python -m pytest -k order     # sirf woh tests jin ke naam mein "order" ho
python -m pytest tests/test_models.py                      # ek file
python -m pytest tests/test_models.py::test_add_message    # ek specific test
python -m pytest --lf         # sirf pichli baar fail hone wale (last failed)
python -m pytest --pdb        # fail hote hi debugger khul jaye
```
> `pytest` ki jagah `python -m pytest` likhein. Windows par ye ghalat Python/env wale masle se bachata hai.

## B.4 `conftest.py`: shared fixtures
**Fixture** = test ke liye tayyar shuda cheez (object, config, fake data). Har test mein dobara banane ki jagah ek baar likhein, aur test ke **argument mein naam** likh dein. pytest khud de de ga.

Har test ko **naya** fixture milta hai, is liye ek test doosre ko kharab nahi karta. Fixture doosre fixture ko bhi use kar sakta hai (`convo(config)`).

▶ `tests/conftest.py` kholein

## B.5 Basic `assert` aur `parametrize`
**`@pytest.mark.parametrize`** = ek test, kai inputs. Har input alag test ki tarah chalta aur report hota hai.

▶ `tests/test_models.py` · `python -m pytest tests/test_models.py -v`

## B.6 Errors test karna (`pytest.raises`) aur files (`tmp_path`)
- **`pytest.raises(ValueError)`:** test tab pass hota hai jab error **aaye**. `match=` se message bhi check hota hai.
- **`tmp_path`:** pytest ka built-in fixture jo har test ko ek **temporary folder** deta hai. Asli files kharab nahi hoti.

▶ `tests/test_config.py`

## B.7 Tools test karna + logs check karna (`caplog`)
- `parametrize` mein **kai values ek saath** (tuple) de sakte hain: `"text, expected"`
- **`caplog`:** check karta hai ke code ne sahi **log message** likha

▶ `tests/test_tools.py`

## B.8 🎭 Mocking: AI engineer ke liye sab se zaroori

Tests mein **asli LLM API call nahi karte**:
| Asli call | Masla |
|---|---|
| 💸 Paise lagte hain | 100 tests × din mein 20 baar = bill |
| 🐢 Slow | Hamari fake call bhi 2 second leti hai |
| 🎲 Har baar alag jawab | `assert reply == "..."` kabhi pakka pass nahi hoga |
| 🌐 Internet/key chahiye | Bina internet tests fail |

**Hal:** `monkeypatch` se asli function ki jagah **fake function** laga dein. Phir hum **apni logic** test karte hain (sahi messages gaye? tool sahi chala?), LLM ko nahi.

### ⚠️ Sab se aham rule: wahan patch karein jahan function **use** hota hai
`main.py` mein likha hai `from bot.llm import ask_llm`. Is ka matlab hai `main` ke paas `ask_llm` ki **apni copy (reference)** hai. Is liye:
- ✅ `monkeypatch.setattr("bot.main.ask_llm", fake)`
- ❌ `monkeypatch.setattr("bot.llm.ask_llm", fake)`. `main` phir bhi asli wala chalaye ga!

▶ `tests/test_main.py`

**Experiment:** `test_main.py` mein `"bot.main.ask_llm"` ko `"bot.llm.ask_llm"` kar ke chalayein. Test 2 second lagaye ga aur fail hoga. Phir wapas theek kar dein.

## B.9 Ab saare tests chalayein 🚀
```
python -m pytest -v
```
**Shuru mein natija: `3 failed, 21 passed`**. Teeno fail `test_pricing.py` mein hain, kyun ke `bot/pricing.py` mein bug hai. Ye Part C.4 ka kaam hai.

## B.10 pytest ka output parhna
- `PASSED` ✅ / `FAILED` ❌ har test ke saath
- `test_apply_discount[1000-10-900]`: brackets mein **parametrize ke inputs**. Isi se pata chalta hai **kaunsa** input fail hua
- Pehla `0%` wala case pass hua, kyunke 0 se zarb dene par bug chhup jata hai. Ye sabaq hai ke **kai inputs** se test karna kyun zaroori hai
- `FAILURES` section mein har fail ka detail hai:
  - `>` wali line jahan `assert` fail hua
  - `E` wali lines mein **asal value vs expected** (jaise `assert -9000 == 900`)
- Aakhir mein summary: `N failed, M passed in X.XXs`

Saare tests **ek second se kam** mein chalte hain, halaanke `ask_llm` 2 second leta hai. Ye mocking ka kamaal hai.

Try karein:
```
python -m pytest -k order -q
python -m pytest -x -q
```

## B.11 Kya test karein, kya nahi? (AI projects)

| ✅ Test karein | ❌ Test na karein |
|---|---|
| Apni logic: parsing, routing, calculation | LLM ka **exact** jawab |
| Prompt sahi bana? Sahi messages gaye? | Third party library khud (jaise `requests` chalta hai ya nahi) |
| History trim, config validation | Asli API call (mock karein) |
| Tool ka result aur error handling | |
| Edge cases: khali input, `None`, ghalat order id | |

**Achhe test ki pehchaan:** chhota, tez, ek hi cheez check kare, aur naam se pata chale kya test ho raha hai (`test_unknown_order_logs_warning`).
