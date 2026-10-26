# M9.1 · Exercise

> Pehle `notes.md` parho, dono scripts chalao, phir ye exercise **khud likh kar** karo.
> Jawab mujhe share karo, main review karunga jaise ek senior engineer design review mein karta hai.

---

## Part A: Apne numbers (scripts se)

`measure_baseline.py` teen dafa chalao aur bharo:

| Run | Quality | p50 latency | p95 latency | Avg reasoning tokens | $/month (1k/day) |
|---|---|---|---|---|---|
| 20b, low | | | | | |
| 120b, low | | | | | |
| 20b, medium | | | | | |

1. Kaun sa config ship karoge? Section 6.2 ke trade-off template mein 3–4 lines likho.
2. Kya koi test FAIL hua? Kyun? Kya ye model ki galti thi ya **eval (keyword check) ki**?
   (Hint: keyword eval kabhi sahi jawab ko bhi fail kar deta hai. Isi liye Level 7 mein LLM-as-judge seekha tha.)
3. `cost_latency_estimator.py` mein `WHATSAPP_BOT` ke token numbers apne real averages se replace karo aur dobara chalao. Monthly cost kitni bani?

## Part B: Decision practice

Har use case ke liye likho: **approach** (prompting / stuffing / RAG / tools / pipeline / agent / fine-tune, ya combination), **1 line kyun**, aur **1 rejected alternative + kyun**.

1. Ek law firm: 20,000 purane case PDFs par sawal-jawab, lawyers ko citation chahiye.
2. Ek restaurant: WhatsApp par menu (1 page) aur timing ke sawal, ~100 msgs/day.
3. Ek e-commerce company: 50,000 product reviews se roz raat ek summary report banani hai.
4. Ek startup: customer ki email padh kar ticket category (billing/tech/sales) assign karni hai, 100,000 emails/day, budget bohat kam.
5. Ek user kehta hai: "Mujhe aisa assistant chahiye jo web par research kare, 10–20 sources padhe, aur report likhe."

## Part C: Estimation (bina script ke, kaghaz par)

Prices: $0.15/M input, $0.60/M output.
Ek internal HR bot: 300 employees, har employee roz ~4 sawal, 9am–6pm.
Har sawal: system prompt 600 + RAG chunks 2,000 + history 400 + question 50 tokens. Output 250 tokens.

1. Cost per request?
2. Cost per month (22 working days)?
3. Average QPS aur peak QPS (5x)?
4. Sab se bara cost lever kaun sa hai, aur kitna bachega agar RAG chunks 2,000 se 800 kar do?

## Part D: Freelance practice

`templates/requirements_template.md` ki copy banao (`my_project_requirements.md`) aur **apne WhatsApp support bot** ke liye bharo.
Ye Level 9 ke capstone (M9.10) ki buniyad banegi, to jitna real data daal sako utna behtar.
