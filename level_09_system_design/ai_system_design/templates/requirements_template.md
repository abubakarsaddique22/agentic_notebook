# AI Project: Requirements & Constraints Template

> Har naye project / client discovery call par is file ki copy banao aur bharo.
> Khaali chhoda hua har sawal = baad mein ek surprise.

**Project:** ____________________  **Client:** ____________________  **Date:** __________

---

## 1. Problem & value
- Abhi ye kaam kaun karta hai, kaise? ______________________
- Is mein kitna waqt / paisa lagta hai (per day / month)? ______________________
- AI se kya behtar hoga? (waqt bachega, 24/7, zyada sales) ______________________

## 2. Users & channel
- User kaun hai? ☐ Customer ☐ Internal staff ☐ Developer ☐ Other: ______
- Channel: ☐ WhatsApp ☐ Web chat ☐ Mobile app ☐ Slack/Teams ☐ API ☐ Email
- Streaming possible? ☐ Haan ☐ Nahi (WhatsApp/SMS/email = nahi)
- Languages: ☐ English ☐ Urdu ☐ Roman Urdu ☐ Other: ______

## 3. Functional requirements (kya karega)
Top 10 kaam / sawal (real examples maango):
1. ______________________
2. ______________________
3. ______________________
4. ______________________
5. ______________________

Actions (kya system kuch **karega** bhi, ya sirf jawab dega?):
- ☐ Sirf jawab ☐ Data read (order status, stock) ☐ Data write (booking, refund, order) ← **high risk, human approval?**

## 4. Success criteria (NUMBER ke saath)
| Metric | Target |
|---|---|
| Auto-resolve rate (bina human) | ____ % |
| Accuracy / correct-answer rate (eval set par) | ____ % |
| Galat/hallucinated answers | < ____ % |
| Latency (p95) | < ____ s |
| Customer satisfaction (thumbs up) | ____ % |

## 5. Traffic
- Requests / day abhi: ______  6 mahine baad: ______
- Busy hours: ______ (e.g. 11am–11pm)
- Peak events: ______ (sale, Eid, launch) → peak multiplier: ____x

## 6. Latency
- User kitna wait karega? ______ s
- Koi kaam background mein ho sakta hai (report, email)? ☐ Haan ☐ Nahi

## 7. Quality & risk
- Galat jawab ki qeemat: ☐ Kam (FAQ) ☐ Medium (paisa/order) ☐ Zyada (medical/legal/financial)
- Citations / source dikhana zaroori? ☐ Haan ☐ Nahi
- Kab human ko handoff hona chahiye? ______________________

## 8. Data & knowledge
| Source | Format | Size | Kitni baar update | Kaun update karta |
|---|---|---|---|---|
| e.g. FAQ | Google Doc | 5 pages | Mahine mein 1 | Owner |
| e.g. Orders | Shopify API | live | real-time | system |
| | | | | |

- Access control: kya har user har data dekh sakta hai? ☐ Haan ☐ Nahi → detail: ______

## 9. Privacy & compliance
- Personal data (naam, phone, address, CNIC)? ☐ Haan ☐ Nahi
- Data third-party LLM provider (Groq/OpenAI) ko ja sakta hai? ☐ Haan ☐ Nahi ☐ Masking ke baad
- Koi data residency / legal requirement? ______

## 10. Budget & constraints
- Build budget: ______
- Monthly running budget (LLM + hosting + channel): ______
- Timeline / deadline: ______
- Kaun maintain karega? ☐ Main (freelancer) ☐ Client ki team ☐ Dono
- Existing tech stack (jo use karna hi hai): ______

## 11. Estimate (cost_latency_estimator.py se)
| | Value |
|---|---|
| Input tokens / request | |
| Output tokens / request (reasoning samet) | |
| Model | |
| Cost / request | |
| Cost / month (normal) | |
| Cost / month (peak month) | |
| Expected latency | |

## 12. Initial approach (decision tree se)
- ☐ Prompting ☐ Context stuffing ☐ RAG ☐ Tools ☐ Deterministic pipeline ☐ Agent ☐ Fine-tuning
- **Baseline kya hoga:** ______________________
- **Rejected (aur kyun):** ______________________

## 13. Phases
| Phase | Scope | Time | Payment |
|---|---|---|---|
| 1. MVP / baseline | | | |
| 2. | | | |
| 3. (data ke basis par) | | | |

## 14. Open questions / risks
- ______________________
