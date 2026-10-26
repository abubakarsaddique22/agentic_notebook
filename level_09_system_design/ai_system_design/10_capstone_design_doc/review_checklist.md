# Design Doc Review Checklist (self-grade)

Har item: ✅ (done, numbers ke saath) / 🟡 (hai lekin vague) / ❌ (missing). Target: koi ❌ nahi, 🟡 ≤ 3.

## Requirements
- [ ] Functional requirements prioritized (P0/P1/P2)
- [ ] Non-functional requirements **numbers** ke saath (latency, availability, cost)
- [ ] Success criteria measurable, aur har ek ka "kaise naapein"
- [ ] Out-of-scope likha hai

## Numbers
- [ ] Traffic: now / growth / peak
- [ ] Back-of-envelope: tokens, cost/request, cost/month, provider limits (RPM/TPM)
- [ ] Latency budget per component (total = target)
- [ ] Cost budget **saare** items (LLM, STT, channel fees, hosting, tools)

## Architecture
- [ ] Diagram jo request ka poora path dikhaye
- [ ] Request walkthrough step-by-step
- [ ] Components ke boundaries/interfaces
- [ ] Har bara faisla: **kyun** + kya reject kiya

## AI-specific
- [ ] Har information ka source decided (model / prompt / RAG / tool / memory), freshness, ACL
- [ ] Model per task + fallback + fallback ka quality risk
- [ ] Workflow vs agent ka justification
- [ ] Tools ke risk tiers + approvals
- [ ] Caching: kya, key, TTL, kya NAHI cache hota

## Production
- [ ] Failure table (kam se kam 8 failures) + user ko kya dikhta hai
- [ ] Timeouts / retries / breaker settings
- [ ] Degradation ladder
- [ ] SLOs (availability, latency, quality)
- [ ] Guardrails per boundary (input, retrieval, output, action)
- [ ] PII, secrets, retention
- [ ] Eval set (size, slices, metrics, gate threshold)
- [ ] Monitoring: metrics, slices, alerts + runbooks, versioning
- [ ] Feedback loop: explicit + implicit + failure → eval process (owner, cadence)
- [ ] Scaling: 10x/100x par kya tootega

## Communication
- [ ] Summary 5–7 lines mein
- [ ] Risks & open questions with owners
- [ ] Rollout plan with exit criteria
- [ ] Assumptions clearly marked

## "Defend" test
Kisi se kaho har section par "kyun?" aur "agar ye fail ho to?" poochhe. Jis sawal ka jawab doc mein nahi, wahan 🟡 lagao.
