# 07 — Prompt Management (Prompt Hub)

## Problem
Prompt code mein hardcoded hai → har chhoti tabdeeli ke liye code change + deploy.
Kaunsa prompt version production mein hai? Purana wala kya tha? Koi nahi jaanta.

## Solution: LangSmith Prompt Hub
- Prompt LangSmith mein store hota hai, **har save = naya commit (version)**
- Commit par **tag** laga sakte ho: `prod`, `staging`
- App `name:prod` pull karti hai → UI mein tag move karo = prompt deploy (bina code deploy)
- **Playground** mein prompt test + experiments directly UI se

## Files
| File | Concept |
|---|---|
| `01_push_prompt.py` | Prompt banake hub par push karna (aur naya version push karna) |
| `02_pull_and_use_prompt.py` | Latest / specific version / tag pull karna, LangChain (ChatGroq) aur OpenAI SDK (Groq URL) dono ke saath use karna, fallback pattern |

## Industry tips
1. Prompt version ko trace **metadata** mein daalo (`prompt_version` / commit) → baad mein version-wise filter
2. App startup par pull + cache karo, har request par nahi
3. Hub down ho to **local fallback** prompt rakho
4. Naya prompt → pehle experiment (folder 06) → phir `prod` tag

## UI
smith.langchain.com → **Prompts** → `watch-support-prompt` → Commits tab, tags, Playground.
