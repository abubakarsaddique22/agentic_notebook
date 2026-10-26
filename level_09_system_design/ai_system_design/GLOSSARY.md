# Glossary: AI System Design terms

Har module ke saath ye file grow hogi. Jab bhi koi term samajh na aaye, yahan dekhein.

## Module 1

| Term | Matlab (simple) | Example |
|---|---|---|
| **Functional requirement** | System **kya** karega | "Order status batana", "return policy ka jawab dena" |
| **Non-functional requirement (NFR)** | System **kaisa** hoga: speed, cost, reliability, privacy | "Jawab 3 second mein", "cost < $20/month" |
| **Constraint** | Wo cheez jo aap change nahi kar sakte | "Data Pakistan se bahar nahi jayega", "budget fixed hai" |
| **Success criteria** | Kaise pata chalega project kamyab hai, **number ke saath** | "70% queries bina human ke resolve hon" |
| **Traffic / QPS** | Kitni requests aati hain. QPS = queries per second | 500 msgs/day ≈ 0.006 QPS avg |
| **Peak traffic** | Sab se zyada busy waqt ka load. Usually avg ka 3–10x | Sale wale din raat 9 baje |
| **Latency** | Request bhejne se jawab milne tak ka waqt | 2.5 seconds |
| **TTFT** | Time To First Token: pehla lafz screen par aane ka waqt | 0.3 s |
| **TPS (output)** | Tokens per second: model kitni tezi se likhta hai | Groq gpt-oss-20b ≈ 1000 tok/s |
| **p50 / p95 / p99** | Percentiles. p95 = 95% requests is se tez hain | p95 latency 4s |
| **Token** | Text ka chhota tukda (~¾ English word). Billing isi par hoti hai | "Lahore" ≈ 1–2 tokens |
| **Input / output tokens** | Jo aap bhejte ho / jo model likhta hai. Output mehnga hota hai | in $0.075/M, out $0.30/M |
| **Baseline** | Sab se simple working version, jis se baad mein compare karein | Ek prompt + FAQ text |
| **Back-of-envelope estimate** | Rough hisaab jo 2 minute mein kaghaz par ho jaye | 500 × 2000 tokens × 30 days |
| **Trade-off** | Ek cheez behtar karne se doosri kharab hoti hai | Bara model → quality ↑, cost ↑, latency ↑ |
| **SLA / SLO** | Service promise. SLO = internal target (99.5% uptime) | "p95 < 3s" |
| **Human escalation / handoff** | Bot khud handle na kar sake to insaan ko de dena | "Agent se baat karwata hoon" |
| **Unit economics** | Ek request / ek user / ek conversation ki cost | $0.0004 per message |

## Module 2: Context & knowledge
| Term | Matlab (simple) | Example |
|---|---|---|
| **Parametric knowledge** | Jo model ne training mein seekha | "3ATM kya hai" |
| **Context stuffing** | Poora (chhota) data seedha prompt mein | 2-page FAQ |
| **Hybrid retrieval** | Vector (meaning) + keyword/BM25 (exact words) | SKU + paraphrase dono pakdo |
| **RRF** (Reciprocal Rank Fusion) | Do rankings ko sirf rank se jodna: Σ 1/(60+rank) | Vector + BM25 fusion |
| **Reranker** | Top-N chunks ko dobara, zyada accurately rank karna | Cross-encoder |
| **ACL / pre-filter** | Retrieval se PEHLE permission filter | customer ko internal docs nahi |
| **Provenance** | Jawab ka source (doc, version, date) | [S1] Return policy v2 |
| **Zombie chunks** | Update ke baad bhi index mein reh gaye purane chunks | Purani policy |
| **Multi-tenant** | Ek system, bohat clients, data alag | Shop A / Shop B |

## Module 3: Routing & gateways
| Term | Matlab | Example |
|---|---|---|
| **Model gateway** | App aur providers ke beech layer | LiteLLM |
| **Model alias** | App jo naam use kare ("fast"), asal model gateway decide kare | fast → gpt-oss-20b |
| **Routing** | Request ko sahi model par bhejna | complaint → smart |
| **Cascade** | Pehle sasta model, fail par mehnga | fast → validate → smart |
| **Fallback** | Primary fail → doosra model/provider | Groq → Ollama |
| **Cooldown** | Fail hone wale deployment ko kuch der skip | 30s |
| **served_by** | Asal mein kis model ne jawab diya | logs mein |

## Module 4: Latency
| Term | Matlab | Example |
|---|---|---|
| **Prefill** | Model input "padhta" hai (TTFT par asar) | 12k tokens → slow TTFT |
| **Decode** | Output tokens ek ek karke banna | 400 tokens |
| **TPOT / ITL** | Time per output token | 1–20 ms |
| **Span** | Ek step ka timed hissa (trace ke andar) | retrieval 0.25s |
| **Waterfall** | Spans ka timeline view | Exp 1 |
| **Little's Law** | concurrency = QPS × latency | 2 × 3 = 6 |
| **RPM / TPM** | Provider rate limits: requests / tokens per minute | 120 RPM |
| **Batch API** | Offline bulk requests, ~50% sasta | Nightly summaries |
| **Speculative decoding** | Chhota model draft, bara verify → tez | Self-hosting |

## Module 5: Caching
| Term | Matlab | Example |
|---|---|---|
| **Exact cache** | Same (normalized) sawal → same jawab | "return policy?" |
| **Semantic cache** | Milta julta sawal (embedding) → cached jawab | paraphrase |
| **Prompt / prefix caching** | Provider repeated prompt prefix ka compute reuse kare | 50% input discount |
| **Cacheability gate** | Pehle check: cache karna safe hai? | order status = nahi |
| **TTL** | Kitni der baad entry expire | 24h |
| **Invalidation** | Purani entries ko hatana / miss karwana | kb_version bump |
| **Entity guard** | Semantic hit tabhi jab IDs/cities/numbers same hon | TW-2041 ≠ TW-2047 |
| **Hit rate / wrong-hit rate** | Kitni requests cache se, kitni galat | 72% / 0 |

## Module 6: Reliability
| Term | Matlab | Example |
|---|---|---|
| **Retryable error** | Dobara try karne se theek ho sakta hai | 429, 503, timeout |
| **Exponential backoff + jitter** | Har retry par wait double + random | 0.5s, 1s, 2s ± |
| **Circuit breaker** | Bohat fails → kuch der primary skip | CLOSED/OPEN/HALF_OPEN |
| **Bulkhead** | Concurrency limit taake ek hissa sab na giraye | Semaphore(20) |
| **Graceful degradation** | Kam quality lekin useful jawab | cached / canned |
| **Fail open / closed** | Fail par chalta rahe / ruk jaye | FAQ / refund |
| **Idempotency** | Same request do dafa = ek hi asar | message_id dedupe |
| **HITL** | Human-in-the-loop approval | refund approval |
| **SLI / SLO / SLA / error budget** | Metric / target / contract / allowed failure | 99.5% |

## Module 7: Orchestration
| Term | Matlab | Example |
|---|---|---|
| **Deterministic pipeline** | Code flow decide karta hai | classify → tool → answer |
| **Workflow vs agent** | Fixed steps vs model khud steps chune | support bot vs research agent |
| **Orchestrator-workers** | Ek LLM kaam baante, workers karein | deep research |
| **Evaluator-optimizer** | Generate → critique → improve | writing |
| **ACK + async** | Foran 200, kaam background mein | WhatsApp webhook |
| **202 Accepted + polling** | Job create, status baad mein | reports |
| **Durable workflow** | Crash ke baad resume hone wala lamba process | Temporal |
| **Composition root** | Ek jagah jahan implementations jodi jaati hain | `app.py` |

## Module 8: Monitoring
| Term | Matlab | Example |
|---|---|---|
| **Trace** | Ek request ka poora record (spans + metadata) | trace_id |
| **Explicit feedback** | User ne khud bataya | 👍/👎 |
| **Implicit feedback** | Behavior se signal | rephrase, "agent chahiye" |
| **Slicing** | Metrics ko groups mein todna | by intent / version |
| **Regression** | Naye version mein quality giri | faq_delivery +34% |
| **CI eval gate** | Deploy se pehle eval pass hona zaroori | ≥ 90% |
| **Canary / shadow** | Thore traffic par naya version / chupke se compare | 5% rollout |
| **Alert fatigue** | Bohat alerts → log ignore karne lagte hain | |

## Channel / platform
| Term | Matlab | Example |
|---|---|---|
| **24-hour customer service window** | User ke message ke 24h tak free-form reply allowed (WhatsApp) | baad mein sirf template |
| **Service message** | Window ke andar business reply. 1 Oct 2026 se 1,000/month free, phir paid | bot ka jawab |
| **Template message** | Pre-approved message, window ke bahar bhi | "Return approved" |
