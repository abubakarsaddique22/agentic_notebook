# M9.5 · Exercise

## Part A: Code
1. `caching_lab.py` Ollama ke saath aur `--offline` dono chalao. EXP 4 ke threshold sweep mein kya farq aaya?
2. `QUERIES` mein ek negation case daalo: ("Do you NOT accept returns on sale items?", ...). Semantic cache kya karta hai? Entity guard isse pakadta hai? Kaise behtar banaoge?
3. `exact_key()` mein `tenant_id` add karo (`CacheConfig` mein naya field). Do tenants ke saath test karo ke ek ka jawab doosre ko na mile.
4. `is_cacheable()` mein Pakistani phone number (03xx...) aur email already hain. CNIC pattern (xxxxx-xxxxxxx-x) bhi add karo.
5. **Bonus:** thumbs-down feedback ka function likho: `cache.purge(query)` jo exact aur semantic dono se entry hata de.

## Part B: Kya cache karoge?
Har item ke liye: cache? kaun sa layer? TTL? key mein kya?
1. "Store timing kya hai?"
2. "TW-2041 stock mein hai?"
3. "Mera order #4521 kab aayega?"
4. Product descriptions ke embeddings
5. Ek user ki 20-message conversation ka summary
6. "Quartz aur automatic mein kya farq hai?"

## Part C: Design
Ek client kehta hai: "Monthly LLM bill $200 hai, kam karo." Aapke paas pichle mahine ke 30,000 messages ke logs hain.
1. Caching lagane se pehle kaun se 3 numbers logs se nikaaloge?
2. Kaun se caches lagaoge, kis order mein, aur kyun?
3. Launch ke baad kaise prove karoge ke bill kitna kam hua, aur quality nahi giri?
