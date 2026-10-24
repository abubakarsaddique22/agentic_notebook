# 🐍 Python AI Engineer Practice (notebooks → .py files)

Do folders, har notebook ka ek:

| Folder | Notebook | Andar kya hai |
|---|---|---|
| `01_http_rest_fastapi/` | HTTP_REST_JSON_FastAPI_AI_Engineer.ipynb | HTTP, status codes, JSON, REST, auth, httpx, FastAPI, mini project, interview Q&A, exercises |
| `02_modules_pytest_debugging/` | Modules_Pytest_Debugging_AI_Engineer.ipynb | Modules/packages, pytest + mocking, debugging, bug hunt, exercises |

**Har folder ka `README.md` pehle parhein.** Us mein setup aur chalane ka order hai.

### Teen baatein jo dono folders mein same hain
1. **Theory** `NOTES*.md` files mein hai (VS Code mein `Ctrl+Shift+V` se preview acha dikhta hai)
2. **Har `.py` file ke upar** likha hai ke usay kaise chalana hai
3. **Hamesha folder ki ROOT se `python -m ...` chalayein** (dots, bina `.py`), jaise:
   ```
   python -m part_a_http_basics.a1_url_parts
   python -m bot.main
   ```
