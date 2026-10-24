# PART D: 🏋️ Exercises

Har exercise mein **asli project files** (`bot/`, `tests/`, `scripts/`) mein khud likhna hai. Atak jayein to `exercises/solutions/` dekhein. **Pehle khud try karein!**

> Shuru karne se pehle Part C.4 ka pricing bug theek kar lein (`NOTES_C_debugging.md`), taake poora test suite green ho.

---

## Exercise 1 (Modules): naya module `bot/faq.py`
- Ek dict `FAQ` banayein: `{"cod": "...", "delivery": "...", "return": "..."}`
- Function `answer_faq(text: str) -> str | None`: agar message mein koi keyword ho to jawab lautaye, warna `None`
- `logger = logging.getLogger(__name__)` lagayein aur jawab milne par `INFO` log karein

Check karein (root se):
```
python -c "from bot.faq import answer_faq; print(answer_faq('Kya COD available hai?')); print(answer_faq('Salam'))"
```
Solution: `exercises/solutions/ex1_faq.py` (copy kar ke `bot/faq.py` bana sakte hain)

---

## Exercise 2 (pytest): `tests/test_faq.py`
- `parametrize` se 3 keywords check karein (bare/chhote huroof dono: `"COD"`, `"cod"`)
- Ek test ke koi keyword na ho to `None`

```
python -m pytest tests/test_faq.py -v
```
Solution: `exercises/solutions/ex2_test_faq.py`

---

## Exercise 3 (Mocking): FAQ ko bot mein jorna
1. `bot/main.py` ke `handle_message` mein: pehle `answer_faq` check ho, agar jawab mile to **LLM call na ho**
2. `tests/test_main.py` mein test likhein jo `ask_llm` ko aisa fake se badle jo **error raise kare** agar chal jaye. Phir `"COD hai?"` bhej kar confirm karein ke FAQ ka jawab aaya aur LLM nahi chala

```
python -m pytest tests/test_main.py -v
python -m bot.main
```
Solution: `exercises/solutions/ex3_main.py` (poora naya `main.py`) aur `exercises/solutions/ex3_test_faq_skips_llm.py` (test jo `test_main.py` ke aakhir mein jorna hai)

---

## Exercise 4 (Debugging): stack trace se bug theek karna
`scripts/crash_demo.py` abhi bhi crash hota hai (C.1). Isay theek karein:
- Agar `order_id` `None` ho to `"Order number bata dein"` lautayein
- `logging` laga kar `WARNING` log karein
- `if __name__ == "__main__":` block mein `logging.basicConfig(...)`

```
python -m scripts.crash_demo
```
Solution: `exercises/solutions/ex4_crash_demo.py`

---

## Aakhri check
```
python -m pytest -q
```
Saare tests pass hon to aap ka `practice_bot` mukammal hai 🎉

**Bonus:** `pip install ruff mypy` phir `ruff check .` aur `mypy bot scripts`. `mypy` C.1 wala `None` bug **chalaye baghair** pakar le ga.
