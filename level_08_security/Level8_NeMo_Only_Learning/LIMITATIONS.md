# NeMo capabilities vs things NeMo alone does NOT provide

| Requirement | NeMo status | What else is needed |
|---|---|---|
| Input/output prompt self-checks | Built in | Strong prompts, capable model, empirical validation |
| Dialog flows | Built in | Colang flows and testing |
| KB retrieval | Built in | Document lifecycle; retrieval rails for chunk checks |
| PII | Built-in rail integration | Presidio / entity detector dependencies and models |
| Jailbreak heuristics | Built-in optional rail | `transformers`, `torch`, model download and calibration |
| NVIDIA jailbreak NIM | Optional NeMo integration | NVIDIA API key and available endpoint/model |
| Tools | NeMo `@action` / Colang execution | Actual business code and real authorization |
| Verified login / identity / tenant isolation | NOT provided by rails alone | SSO, server-side RBAC/ABAC and trusted identity |
| Human approval for dangerous actions | NOT a turnkey native approval system | Approval service + records + server-enforced decisions |
| Database, immutable audit log and SIEM | NOT a full built-in platform | Database, observability pipeline and policy |
| Production-grade egress/DLP enforcement | NOT guaranteed by self-checks | Network policy, secret management and DLP controls |
| Automated adversarial red-team campaign / CI scoring | NOT the same as built-in NeMo rails | Own evaluation harness or dedicated external tooling (intentionally excluded) |
| Full RAG grounding and factuality guarantee | NOT guaranteed | Evaluation, citations, policies and appropriate rails |
| Safe execution of arbitrary external actions | NOT guaranteed | Sandboxing, allowlists, authentication, approval |

## What was intentionally removed
Promptfoo (`promptfooconfig.yaml`, providers, redteam runs), LangChain/LangGraph agent, Chroma, SQLAlchemy approval simulator, Presidio standalone service scripts, old tests tied to those components, and non-NeMo policy engines. Optional detectors that NeMo internally integrates are clearly labelled as dependencies instead of pretending they're NeMo-only algorithms.

**Important:** These examples have not been live-tested against your Ollama server or your Windows installation here; offline file checks do not certify NeMo behavior.
