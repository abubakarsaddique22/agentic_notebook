# 05 — Datasets

## Concept
**Dataset** = test cases ka collection. Har **item** mein:
- `input` — app ko kya diya
- `expected_output` — sahi / reference jawab (optional, evals ke liye useful)
- `metadata` — category, split, difficulty wagera
- `source_trace_id` — agar item kisi production trace se bana (UI mein link)

## LangSmith se farq
| LangSmith | Langfuse |
|---|---|
| examples | **items** |
| `outputs` | `expected_output` |
| splits (`train`/`test`) | built-in splits nahi → `metadata={"split": "..."}` + code mein filter |
| version tags (`prod`) | `get_dataset(name, version=<datetime>)` — kisi bhi waqt ka snapshot |
| example delete | item **archive** (`status="ARCHIVED"`) — history bachi rehti hai |
| — | **folders**: naam mein slash, e.g. `support/faq-golden` |

## Industry mein dataset kahan se aata hai?
1. Haath se 20-50 important sawal (start yahin se)
2. Production traces se (file 02) — khaas kar **negative score** wale
3. UI mein trace par **"Add to dataset"** button
4. Annotation queues (human review) ke baad

## Files
| File | Concept |
|---|---|
| `01_create_dataset.py` | Dataset + items (stable `id` se idempotent — dobara chalao to duplicate nahi) |
| `02_dataset_from_traces.py` | Production observations query karke dataset items banana (`source_trace_id` ke saath) |
| `03_versions_and_archive.py` | Split filter, item update, archive, purana version padhna |

> Pehle `01` chalao — folder 06 isi dataset (`watch-support-qa`) ko use karta hai.

## UI
cloud.langfuse.com → **Datasets** → `watch-support-qa` → Items tab, har item ka history.
