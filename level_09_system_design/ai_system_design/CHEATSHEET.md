# Level 9 · AI System Design: 1-Page Cheat Sheet

Interview / client call se pehle 5 minute mein revise karo.

## The framework (M9.1)
**Requirements → constraints → estimate → approach → BASELINE → measure → iterate (only where numbers say) → defend.**
"Earn your complexity." Har decision: *kyun ye, kyun wo nahi, kab revisit.*

## Back-of-envelope
```
cost/req  = (in_tok × in_price + out_tok × out_price) / 1M        (reasoning tokens = output!)
cost/mo   = cost/req × req/day × 30        + channel fees + hosting
avg QPS   = req/day ÷ (busy_hours × 3600) ;  peak ≈ 3–10× avg
latency   ≈ network + retrieval + tools + TTFT + out_tok/TPS
concurrency (Little) = QPS × latency ;  TPM = QPS × 60 × tokens/req
```

## Approach decision (M9.1)
| Problem | Tool |
|---|---|
| Behavior / format / tone | Prompting → (fine-tune last) |
| Small stable knowledge | Context stuffing + prompt caching |
| Big / changing knowledge | RAG (hybrid + metadata) |
| Live data (order, stock, price) | **Tool / API** |
| Fixed steps | Deterministic pipeline |
| Open-ended steps | Agent (with budgets) |

## Knowledge (M9.2)
Sources: model · prompt · RAG · memory · tools. **Metadata = design:** source, version, updated_at, ACL, tenant.
ACL = **pre-filter**, role from auth. Freshness = versioning + delete old chunks. Hybrid + RRF default. Fixed context budget.

## Routing & gateway (M9.3)
Never hard-code a model. Gateway: keys, routing, retries, timeouts, fallbacks, budgets, cost ledger.
Rules → classifier → learned router. **Cascade** works only if pass rate high; validator deterministic first.
Fallback = quality risk → eval every model, log `served_by`.

## Latency (M9.4)
Measure per span, p95. Output tokens = biggest driver. Stream (or typing indicator). Parallelize independent work.
Merge/remove LLM calls. Smaller model if eval passes. Batch API offline.

## Caching (M9.5)
Exact · semantic · retrieval · prompt/prefix · tool. Gate: no personal/live/high-risk.
Key = query + model + prompt_v + kb_v + tenant. TTL + version bump. Semantic = entity guard + high threshold.
**Static prompt first.** Measure hit + wrong-hit rate.

## Reliability (M9.6)
Timeouts everywhere + total budget. Retry only 429/5xx/timeout, backoff + jitter, one layer. Circuit breaker.
Degrade: primary → fallback → cache → reduced → human → honest "can't". High-risk = human approval, fail closed, idempotency.
Guards at boundaries: input · retrieval · output schema · output content · action. SLOs: availability + latency + **quality**.

## Orchestration (M9.7)
Code decides; model only for language/open-ended. Patterns: chain · routing · parallel · orchestrator-workers · evaluator · agent (last).
Sync / ACK+async (webhooks + idempotency) / queue / job (202 + poll) / durable workflow / batch. Interfaces + composition root.

## Monitoring (M9.8)
Trace = input, output, route, level, **all versions**, per-span latency, tokens, cost, cache, tools.
Explicit (sparse) + implicit (noisy) feedback. **Slice, don't average.** Failures → labeled eval cases → CI gate.
Deploy → observe → feedback → evaluate → improve → redeploy.

## Interview flow (M9.9)
Clarify (5) → numbers (3) → baseline (4) → architecture (13) → deep dive (10) → failures/scale/monitoring (7) → trade-offs (3).

## Trade-off sentence
> "I chose **X** because requirement **Y**. **Z** would improve **[a]** but cost **[b]**. If **[condition]**, I'd switch to **Z**."
