# M9.10 · Capstone: AI System Design Document

> **Goal:** Ek substantial AI product ka complete design document, jo aap **AI system-design interview**
> ya **engineering architecture review** mein defend kar sako.

## Is folder mein

| File | Kya hai | Kaise use karna |
|---|---|---|
| `design_doc_template.md` | **Reusable template** (khaali) | Har naye client project / interview practice ke liye copy karo |
| `whatsapp_support_bot_design.md` | **Filled example:** aap ke WhatsApp support bot ka design | Padho, `[ASSUMPTION]` wale numbers apne real data se replace karo, phir isse apna banao |
| `review_checklist.md` | Self-review rubric | Doc complete hone ke baad khud grade karo (ya mujhe bhejo) |

## Roadmap ki requirements → doc ke sections

| Required by roadmap | Section in design doc |
|---|---|
| Requirements and success criteria | §2 |
| Expected traffic and constraints | §3 |
| High-level architecture (+ diagram) | §4 |
| Model choice and routing | §5 |
| Context / RAG architecture | §6 |
| Tools / agents where required | §7 |
| Caching strategy | §8 |
| Latency and cost budget | §9 |
| Reliability and fallback strategy | §10 |
| Security / guardrails | §11 |
| Evaluation and monitoring | §12 |
| User-feedback loop | §13 |
| Scaling strategy | §14 |
| Major trade-offs + rejected alternatives | §15 |

## Kaise complete karein (recommended)

1. `whatsapp_support_bot_design.md` poora padho. Har section ke saath us module ke notes link hain.
2. `[ASSUMPTION]` tags dhoondo (`Ctrl+F`). Har ek ko apne real numbers se replace karo: traffic, FAQ size, product count, Pakistan ka Meta rate, AWS instance.
3. M9.1 ka `measure_baseline.py` apne real FAQ ke saath chalao, aur §9 ke numbers update karo.
4. Diagram ko apne real components ke mutabiq adjust karo.
5. `review_checklist.md` se grade karo.
6. **Mock review:** kisi dost ko (ya mujhe) doc do aur kaho "har decision par 'kyun?' poocho". Jahan jawab na ho, wahan doc mein kami hai.

> 💼 Freelancing mein yahi doc (thora simplify karke) **client proposal** ka technical hissa ban jata hai.
