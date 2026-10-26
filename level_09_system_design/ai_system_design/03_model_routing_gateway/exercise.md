# M9.3 · Exercise

## Part A: Code
1. `gateway.py --mock` chalao, phir real mode mein. Ledger ki cost aur latency compare karo.
2. Real mode mein `MODEL_LIST` mein `fast` ka model `groq/does-not-exist` karo. Demo 2 ka `served_by` kya aaya? Latency kitni badhi (retries ki wajah se)?
3. `choose_route()` mein ek naya signal add karo: `latency_slo_ms`. Agar < 1000 ho to hamesha `fast`, chahe task complaint ho.
4. `validate()` mein ek deterministic check add karo: agar answer mein "Rs" ke saath koi price ho jo context mein **nahi** hai, to fail (hallucinated price).
5. **Bonus:** `UsageLedger.report()` mein har tenant ka "% traffic served by fallback" column add karo.

## Part B: Hisaab
Fast model: $0.0003/request, 1.2s. Smart model: $0.0012/request, 2.5s. 10,000 requests/day.
1. Smart-only ki monthly cost?
2. Cascade, 85% pass rate: monthly cost? Average latency?
3. Cascade, 40% pass rate: monthly cost? Average latency? Kya ye cascade worth it hai?

## Part C: Design
Aap 5 dukanon ke WhatsApp bots chala rahe ho. Ek din Groq 2 ghante down raha.
1. Aapka fallback plan kya hota? Kaun si requests fallback model par, kaun si human queue mein?
2. Client ko kya message jata?
3. Ye kaise ensure karoge ke fallback model Roman Urdu mein bhi theek jawab de?
