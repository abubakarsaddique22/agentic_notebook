# M9.2 · Exercise

## Part A: Code ke saath khelo
1. `knowledge_pipeline.py` normal (Ollama) aur `--offline` dono mein chalao. Demo 5 mein vector results mein kya farq aaya? Kyun?
2. `DOCS` mein ek naya doc daalo: "Eid sale: 20% off till 2026-11-05" (`valid_until` metadata ke saath). Phir `_where()` mein aisa filter add karo ke expire hone ke baad wo retrieve na ho.
3. `assemble_context` mein `token_budget=300` ko `60` karo. Kitne chunks gaye? Quality par kya asar hoga?
4. `route_knowledge()` mein ek naya route add karo: agar message mein "price" aur koi SKU (TW-xxxx) ho, to `TOOL:get_live_price`. Kyun ye RAG se behtar hai?
5. **Bonus:** Ek `min_score` threshold add karo taake irrelevant chunks (jaise return sawal par delivery doc) context mein na jayein.

## Part B: Design decisions
Har item ke liye source likho (model / system prompt / stuffing / RAG / tool / memory / SQL) aur 1 line kyun:

1. Store ka WhatsApp number aur timing
2. 400 products ki descriptions
3. Kisi product ka current stock
4. Customer ne pichle hafte kaun si watch order ki thi
5. "Pichle mahine sab se zyada kaun si watch biki?"
6. "Quartz aur automatic movement mein kya farq hai?"
7. Refund ka internal SOP (sirf staff ke liye)

## Part C: Scenario
Aap 3 alag dukanon (A, B, C) ke bots ek hi server aur ek hi Chroma instance par chalana chahte ho.
1. Data isolation kaise karoge? (2 options likho, aur dono ke trade-offs)
2. Shop A ki policy update hui. Sirf A ka index kaise refresh hoga?
3. Agar galti se B ka data A ke customer ko chala gaya, to kis layer ki galti thi, aur kaise roka ja sakta tha?
