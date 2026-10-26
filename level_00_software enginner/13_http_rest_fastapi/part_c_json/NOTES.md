# PART C: JSON

> Is part ke liye server ki zaroorat **nahi**.

**JSON (JavaScript Object Notation)** = data ko **text** mein likhne ka format jo har programming language samajhti hai. Web APIs, LLM tool calls, config files aur datasets, sab JSON mein hote hain.

## C.1 JSON ↔ Python

| JSON | Python | Note |
|---|---|---|
| `{"a": 1}` object | `dict` | Keys **hamesha string** |
| `[1, 2]` array | `list` | |
| `"text"` | `str` | Sirf **double quotes** `"` |
| `10`, `3.5` | `int`, `float` | |
| `true` / `false` | `True` / `False` | Chhote huroof |
| `null` | `None` | |
| ❌ | `datetime`, `set`, `tuple`, `Decimal` | Khud convert karna parta hai |

| Function | Kaam |
|---|---|
| `json.loads(text)` | JSON **string** → Python |
| `json.dumps(obj)` | Python → JSON **string** |
| `json.load(f)` / `json.dump(obj, f)` | **File** se parhna/likhna |
| `response.json()` | HTTP response body → Python |

**Yaad rakhein:**
- Urdu text ke liye `ensure_ascii=False`, warna `آ` jaisa kachra aata hai
- `datetime` ko `.isoformat()` se string banayein (`"2026-10-22T14:30:00"`)
- Key na ho to `data["x"]` → `KeyError`. Safe: `data.get("x", default)`

▶ `python -m part_c_json.c1_json_basics`

## C.2 JSON Lines (`.jsonl`): AI datasets ka format

**Har line ek alag JSON object.** Fine-tuning datasets, eval results, chat logs aur batch API files isi format mein hote hain. Fayda: bari file ko **line by line** parh sakte hain, poori memory mein load kiye baghair.

```
{"messages": [{"role": "user", "content": "COD hai?"}, ...]}
{"messages": [{"role": "user", "content": "Delivery kab?"}, ...]}
```

▶ `python -m part_c_json.c2_jsonl` (ye `part_c_json/train.jsonl` bana kar parhe gi)

## C.3 🤖 LLM ke JSON output ko parse aur validate karna (real kaam)

LLM se JSON maango to woh aksar:
- ```` ```json ```` code fence mein lapet deta hai
- Pehle ya baad mein extra text likh deta hai ("Here is the JSON: ...")
- Field bhool jata hai ya ghalat type deta hai

**Hal:** (1) JSON nikaalo → (2) `json.loads` → (3) **Pydantic** se validate karo → (4) fail ho to handle karo (retry ya fallback).

> Production mein pehle provider ka **structured output / JSON mode / tool calling** use karein. Ye safety net phir bhi rakhein.

▶ `python -m part_c_json.c3_llm_json_parse`
