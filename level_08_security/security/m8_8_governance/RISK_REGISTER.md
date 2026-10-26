# Risk Register: TimeHouse Support Agent

Likelihood/Impact: L / M / H. Residual = after the listed control.

| ID | Risk | Asset | L | I | Control (module) | Residual |
|----|------|-------|---|---|------------------|----------|
| R1 | Cross-customer data access (BOLA) | Other PII | H | H | Ownership check in code (M8.4) | Low |
| R2 | Unauthorised / oversized refund | Money | H | H | Amount cap + approval gate (M8.4) | Low |
| R3 | System-prompt secret leak | Coupon | H | M | Secret removed from prompt (M8.6) | Very low |
| R4 | Indirect injection via poisoned doc | PII, reputation | M | H | Poison scan + fencing + allow-list (M8.5/M8.2) | Low-Med |
| R5 | Data exfiltration via email | PII | H | H | Recipient allow-list (M8.4) | Low |
| R6 | Internal docs leak through RAG | Business data | M | M | Audience filter (M8.5) | Low |
| R7 | Harmful / off-brand output | Reputation | M | M | Llama Guard moderation (M8.3) | Med |
| R8 | Runaway tool loop (cost/DoS) | Availability, cost | L | M | Step + time limits (M8.4) | Low |
| R9 | PII copied into logs/traces | PII | M | M | Sanitised logging (M8.6) | Low |
| R10 | Provider retains/trains on data | PII | M | H | Fake data only + provider note (M8.6/M8.8) | Low (this project) |
| R11 | Novel jailbreak bypasses guardrails | Varies | M | M | Defence in depth + red teaming + regression tests (M8.7) | Med, monitored |

## Accepted residual risks
- R7 and R11 are reduced, not eliminated. No guardrail stack catches every novel
  attack. We accept this for a learning project; a production store would add
  monitoring, alerting and periodic red-team runs.
