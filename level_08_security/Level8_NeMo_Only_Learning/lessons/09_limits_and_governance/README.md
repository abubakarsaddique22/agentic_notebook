# Threat modeling, limits and governance

## Concept (Roman Urdu)
Security tests, approval trails, verified identity, audit retention and policy governance are cross-system practices, not magically provided by NeMo.

**NeMo mein kya seekho:** `RailsConfig.from_path()` YAML/Colang ko load karta hai; `LLMRails(config)` rail runtime hai; `generate(messages=...)` input se output tak configured rails chalata hai. Configuration ko har class ke `config/` mein dekho. `config.yml` main LLM/rails specify karta hai, `prompts.yml` model-judge instructions provide karta hai, `.co` dialog/action flow declare karta hai, aur `actions.py` native custom action register karta hai.

## Windows CMD exercise
```cmd
python -m pytest -q
```
**Expected:** Static checks pass; no model-safety pass is claimed.

## Verify carefully
1. Ek normal helpdesk question run karo; answer aur latency note karo.
2. Ek adversarial ya out-of-scope question run karo; actual result save karo.
3. YAML mein **sirf relevant rail** toggle karke difference dekho; judge may give false positive/negative.
4. Model ko exact expected response dene ki guarantee nahi; test findings manually record karo.

## Scope
NeMo built-in features / custom Python NeMo actions ko distinguish karo. Colang 1 examples ko Colang 2 syntax ke saath mix na karo. `--once` bhi actual LLM call karta hai, mock nahi.
