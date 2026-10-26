# Model Card: TimeHouse Support Agent

## Intended use
- Answer customer questions about TimeHouse orders, shipping, returns, warranty.
- Perform limited actions for the logged-in customer: look up their own order,
  email a copy to their own address, request a refund on their own order.

## Not intended for
- Any customer accessing another customer's data.
- Financial advice, medical/legal advice, or general open-domain chat.
- Autonomous high-value actions without human approval.

## System
- App model: Groq `openai/gpt-oss-120b` (hosted inference).
- Embeddings: Ollama `all-minilm` (local).
- Moderation: Llama Guard 3 (local via Ollama).
- Framework: LangChain `create_agent` (LangGraph).
- Retrieval: Chroma over store policy docs, audience-filtered.

## Known limitations & risks
- LLMs can hallucinate; policy answers may be wrong -> provenance shown, humans for edge cases.
- Prompt injection and jailbreaks are never fully solved -> layered defences, not a single prompt.
- Tool actions can cause real harm -> code-level authorization, limits, approval gate.
- Bias/fairness: responses may vary in tone; monitored informally in this learning project.

## Human oversight
- Refunds over PKR 5,000 require human approval (queued, not executed).
- All tool calls and blocks are logged to a sanitised audit trail.

## Data & privacy
- Only fake test data is used.
- Groq free tier has NO contractual zero-retention or no-training terms, so NO
  real customer PII may be sent to it. A production deployment would need a
  provider tier with private connectivity and zero-retention, or a self-hosted model.
- PII is redacted (Presidio) before entering the model context and before logging.

## Evaluations
- Security: attack-success rate from `m8_7_red_teaming/attack_suite.py`.
- Regression: `tests/security/` must stay green on every change.

## Versioning
- Prompt version, model id and defence config are stamped on each run via
  `m8_8_governance/versioning.py` and recorded in the audit log.

## Regulatory note
- EU AI Act: a customer-facing assistant is limited-risk -> transparency
  (tell users it's an AI) and logging obligations apply, not high-risk controls.
- Pakistan has no comprehensive AI law yet (as of this project); the Personal
  Data Protection Bill, if enacted, would govern the PII handling above.
