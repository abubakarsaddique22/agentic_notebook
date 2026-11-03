# NeMo knowledge base / retrieval

## Concept (Roman Urdu)
NeMo can load markdown knowledge-base files from config/kb. Retrieval rails are separate from merely having KB files.

**NeMo mein kya seekho:** `RailsConfig.from_path()` YAML/Colang ko load karta hai; `LLMRails(config)` rail runtime hai; `generate(messages=...)` input se output tak configured rails chalata hai. Configuration ko har class ke `config/` mein dekho. `config.yml` main LLM/rails specify karta hai, `prompts.yml` model-judge instructions provide karta hai, `.co` dialog/action flow declare karta hai, aur `actions.py` native custom action register karta hai.

## Windows CMD exercise
```cmd
python app.py --lesson retrieval --once "When are IT support hours?"
```
**Expected:** Expect response grounded in local KB when retrieval activates. Inspect actual response.

## Verify carefully
1. Ek normal helpdesk question run karo; answer aur latency note karo.
2. Ek adversarial ya out-of-scope question run karo; actual result save karo.
3. YAML mein **sirf relevant rail** toggle karke difference dekho; judge may give false positive/negative.
4. Model ko exact expected response dene ki guarantee nahi; test findings manually record karo.

## Scope
NeMo built-in features / custom Python NeMo actions ko distinguish karo. Colang 1 examples ko Colang 2 syntax ke saath mix na karo. `--once` bhi actual LLM call karta hai, mock nahi.
