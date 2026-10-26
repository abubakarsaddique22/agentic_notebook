# PART E: 📌 Summary aur Cheat Sheet

## Modules & Packages
| Cheez | Yaad rakhein |
|---|---|
| Module | Ek `.py` file |
| Package | Folder + `__init__.py` |
| Import | `from bot.models import Conversation` (absolute, specific) |
| Relative import | `from .models import X`, sirf package ke andar |
| Chalana | Project root se `python -m bot.main` |
| `if __name__ == "__main__":` | Import par na chalne wala code |
| Design rule | Har module ka ek kaam, imports ek taraf behein (no circular) |
| Naam | Apni file ko `json.py`, `random.py`, `openai.py` naam na dein |

## pytest
```
python -m pytest -v           # sab, detail ke saath
python -m pytest -x           # pehle fail par ruko
python -m pytest -k naam      # filter
python -m pytest --lf         # sirf pichle fail
python -m pytest --pdb        # fail par debugger
```
| Tool | Kaam |
|---|---|
| `assert` | Check |
| `pytest.raises(Err, match=...)` | Error aana chahiye |
| `@pytest.mark.parametrize` | Ek test, kai inputs |
| `@pytest.fixture` + `conftest.py` | Shared setup |
| `tmp_path` | Temporary folder |
| `caplog` | Logs check |
| `monkeypatch.setattr("module.jahan_use_hua.func", fake)` | Mocking (LLM, APIs) |

## Debugging
| Masla | Hathiyar |
|---|---|
| Crash | Stack trace: **neeche se upar**, apni file dhoondo |
| Ghalat result | Breakpoint (VS Code `F9` → `F5` → `F10`/`F11`) |
| Production mein kya hua | `logging`: `getLogger(__name__)`, levels, file handler |
| Test fail | `python -m pytest --pdb` ya VS Code "Debug Test" |
| Notebook crash | Agle cell mein `%debug` |

**Workflow:** Reproduce → Isolate → Inspect → Fix → Verify (+ regression test)

## Apne WhatsApp bot mein kahan use karein
1. **Structure:** `config.py`, `models.py`, `llm.py`, `shopify.py`, `faq.py`, `main.py` mein taqseem karein
2. **Tests:** order id parsing, FAQ matching, history trimming, webhook validation. LLM aur Shopify calls ko **mock** karein
3. **Logging:** har message, tool call, LLM latency/tokens. Tokens aur customer data mask karein
4. **Debugging:** webhook ka ajeeb payload aaye to us ka test bana kar `--pdb` se dekhein

**Agla qadam:** `ruff` aur `mypy` ko is project par chalayein. `mypy` C.1 wala `None` bug **chalaye baghair** pakar le ga. 🚀
