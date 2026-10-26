# M9.6 · Exercise

## Part A: Code
1. `reliability.py` chalao. Demo 8 mein `CircuitBreaker(3, reset_after_s=1.0)` ko `reset_after_s=0.3` aur `3.0` karke dekho. Primary % aur primary calls mein kya farq aaya? Kaun sa behtar hai, aur kyun?
2. `Chaos` mein `p_429=0.5` karo (bohat zyada rate limiting). Kya availability giri? Retries kitne bache?
3. `output_guard()` mein ek naya check: agar answer mein koi `Rs <number>` hai jo user ke diye context mein nahi, to block.
4. Human queue mein `draft_flag` field hai. Isse print karo: approval wale ko dikhna chahiye ke draft mein kya risky tha.
5. **Bonus:** `_call_with_retry` mein ek global **retry budget** add karo: last 10s mein total retries 20 se zyada hon to aur retry mat karo (seedha fallback).

## Part B: Failure plan
Apne WhatsApp bot ke liye ek table banao: har row ek failure (kam se kam 8): Groq down, Groq 429, Shopify API down, Meta webhook duplicate message, bad JSON, customer gaali de, customer refund maange, bot loop (do bots aapas mein).
Columns: detect kaise, user ko kya dikhe, system kya kare, log/alert kya ho.

## Part C: SLOs
Apne bot ke liye 4 SLOs likho (availability, latency, quality, degradation). Har ek ka number, aur har ek kaise naapoge.
