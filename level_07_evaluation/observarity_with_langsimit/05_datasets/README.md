# 05 — Datasets

## Concept
**Dataset** = test cases ka collection. Har **example** mein:
- `inputs`  — app ko kya diya (e.g. `{"question": "..."}`)
- `outputs` — expected / reference answer (optional, lekin evals ke liye bohat useful)
- `metadata` — category, difficulty, source wagera
- `split` — `train` / `test` / `edge-cases` jaisi groups

Datasets se hi **evaluation** (folder 06) hoti hai. Bina dataset ke "mera prompt behtar hua?" ka jawab sirf andaza hai.

## Industry mein dataset kahan se aata hai?
1. **Haath se** — 20-50 important sawal (start yahin se karo)
2. **Production traces se** — achhe/bure real conversations (file 02)
3. **User feedback** — thumbs-down wale traces → dataset → fix → re-evaluate
4. **Synthetic** — LLM se variations banwana

## Files
| File | Concept |
|---|---|
| `01_create_dataset.py` | Dataset + examples code se banana (idempotent) |
| `02_dataset_from_traces.py` | Production traces ko query karke dataset mein daalna |
| `03_splits_and_versions.py` | Splits filter karna, dataset version ko tag (`prod`) karna |

> Pehle `01` chalao — folder 06 isi dataset (`watch-support-qa`) ko use karta hai.

## UI
smith.langchain.com → **Datasets & Experiments** → `watch-support-qa`
- Examples tab, splits, versions dekho
- Kisi trace par **"Add to Dataset"** button bhi hota hai (manual curation)
