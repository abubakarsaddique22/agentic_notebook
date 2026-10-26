# 07 — Prompt Management

## Problem
Prompt code mein hardcoded → har tabdeeli ke liye code change + deploy. Kaunsa version live hai? Pata nahi.

## Langfuse Prompt Management
- Har `create_prompt` (same naam) = **naya version** (1, 2, 3...)
- **Labels**: `production` (default jo `get_prompt` laata hai), `staging`, `latest` (khud lagta hai) ya apne
- App `get_prompt("name")` → `production` label wala version. UI mein label move karo = **prompt deploy, bina code deploy**
- **config**: prompt ke saath model, temperature, wagera bhi store (product team bina code ke tune kar sake)
- Variables: `{{variable}}` (double curly braces) → `prompt.compile(variable=...)`
- **Client-side cache** (default 60s) → har request par network call nahi. Langfuse down ho to **fallback**.
- Generation ko prompt se **link** karo → UI mein har prompt version ki latency, cost, scores

## LangSmith se farq
| LangSmith Prompt Hub | Langfuse |
|---|---|
| commits (hash) | versions (number) |
| tags (`prod`) | labels (`production`) — default yahi fetch hota hai |
| `{var}` | `{{var}}` (LangChain ke liye `get_langchain_prompt()` convert karta hai) |
| prompt object LangChain template | text ya chat prompt + **config** |

## Files
| File | Concept |
|---|---|
| `01_create_prompts.py` | text + chat prompts, versions, labels, config, commit message, label promote |
| `02_use_with_openai.py` | get_prompt (label/version), compile, config use karna, fallback + cache, **trace se link** |
| `03_use_with_langchain.py` | `get_langchain_prompt()` + LangChain mein link |

## Industry tips
1. Naya prompt → label `staging` → experiment (folder 06) → behtar ho to `production` label
2. Rollback = purane version par `production` label wapas
3. Hamesha `fallback` do — Langfuse kabhi down ho to bhi app chale
4. `production` fetch karo, `latest` nahi (latest = jo abhi kisi ne save kiya, untested)

## UI
**Prompts** → `watch-support` → versions, labels, **Playground** (prompt test), metrics tab.
