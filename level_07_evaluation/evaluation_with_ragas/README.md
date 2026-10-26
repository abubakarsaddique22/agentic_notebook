# LLM Evaluation Suite (RAGAS) — RAG Teaching Assistant + Support Agent

A complete, level-by-level evaluation suite for two LLM applications, built with **RAGAS v0.4** and an
open-weight judge (**gpt-oss:20b via Ollama**):

1. **RAG teaching assistant** — answers questions about an LLM-evaluations course from 8 lecture transcripts
   (Chroma + cross-encoder reranker + grounded, citation-capable generator).
2. **Tool-calling support agent** — a watch-store customer-support agent (orders, tracking, cancellations,
   refunds via human escalation) running against a mock store with injectable failures.

The same apps were also evaluated with DeepEval in a sibling project; `compare_frameworks.py` puts both
frameworks side by side.

---

## What is evaluated

| Level | File | What it checks | How |
|---|---|---|---|
| **1. Component** | `evals/01_component_level/eval_retriever.py` | Retriever finds the right context, ranked well | RAGAS ContextRecall, ContextPrecision |
| | `evals/01_component_level/eval_generator.py` | Generator stays grounded on *golden* context | RAGAS Faithfulness, AnswerRelevancy |
| **2. Pipeline** | `evals/02_pipeline/eval_rag_pipeline.py` | RAG Triad end-to-end + **root cause** (retrieval vs generation) | ContextRelevance, Faithfulness, AnswerRelevancy |
| **3. Application** | `evals/03_application/eval_application.py` | Correct, complete, on-style answers; latency | AnswerAccuracy, FactualCorrectness (recall), DiscreteMetric |
| | `evals/03_application/eval_citation.py` | Citations present, not invented, actually supporting | code + DiscreteMetric |
| **4. Safety** | `evals/04_safety/eval_toxicity.py` | No toxic output under attack; no over-refusal on benign | DiscreteMetric judges |
| | `evals/04_safety/eval_leakage.py` | No system-prompt / transcript / PII leakage | code (canaries, 8-gram overlap, PII regex) + judge |
| | `evals/04_safety/eval_scope.py` | Declines off-topic work, answers course parts of mixed requests | action judge + per-case criteria |
| | `evals/04_safety/eval_indirect_injection.py` | Poisoned retrieved chunk can't hijack the bot | canary check + behaviour judge |
| **5. Operations** | `evals/05_operations/eval_ops.py` | p50/p95 latency, TTFT, tokens, cost, errors, answer consistency + SLOs | captured signals + SemanticSimilarity |
| **6. Regression** | `evals/06_regression/run_suite.py`, `compare.py` | Versioned runs, baseline comparison, **CI quality gate** (exit 1 on regression) | metric deltas with tolerance |
| **7. Online** | `evals/07_online/simulate_traffic.py`, `online_eval.py` | Log → stratified sample → reference-free scoring → dashboard → alerts → failures fed back to goldens | Faithfulness, AnswerRelevancy, ContextRelevance |
| **8. Agent** | `evals/08_agent/eval_agent.py` | Tool selection & args, trajectory, goal completion, end state, denied tools, failure recovery, step budget | ToolCallF1, ToolCallAccuracy, AgentGoalAccuracy + code |
| **9. Model selection** | `evals/09_model_selection/eval_model_selection.py` | Pick the best-value model for *our* task (Text-to-SQL) | execution accuracy, DataCompyScore, SQLSemanticEquivalence, latency, tokens |

Design rule used throughout: **if code can check it, code checks it** (canaries, PII, end state, SQL results);
the LLM judge is used only for semantic questions.

---

## Results (latest run)

| Area | Key metrics |
|---|---|
| Retriever | context recall **0.98**, context precision **0.90** |
| Generator (golden context) | faithfulness **0.94**, answer relevancy **0.77** |
| Pipeline (RAG Triad) | context relevance **1.00**, faithfulness **0.93**, answer relevancy **0.63** |
| Application | answer accuracy **0.97**, completeness **0.72**, style pass **87%** |
| Citations | present / valid / supported **100%** |
| Safety | toxicity **100%** safe, leakage **100%** safe, scope **87%** |
| Indirect injection | **3/8 pass** ← main weakness |
| Agent | tool-call F1 **0.74**, goal accuracy **54%**, end state **69%**, denied tools never called **100%** |
| Operations | latency p50 **9.5s** / p95 **13.4s**, TTFT p95 **7.3s**, 0 errors |

**Findings**
- Retrieval is strong; the pipeline's weak spot is **answer relevancy** (root cause: generation answers
  around the question rather than retrieval failing).
- Completeness (0.72) lags correctness (0.97): answers are right but skip points from the ideal answer.
- **Indirect prompt injection** is the most serious issue: a poisoned chunk made the bot reveal internal
  prompt details, push an external link and echo a fake "admin mode" string.
- The agent never calls forbidden tools, but completes only about half the goals cleanly.

---

## Setup (Windows)

```bat
conda activate genai
pip install -r requirements.txt

ollama pull nomic-embed-text
ollama pull all-minilm
```

The generator, agent and judge use `gpt-oss:20b-cloud` through the local Ollama daemon.
RAG embeddings: `nomic-embed-text` (set `RAG_EMBED_PROVIDER=openrouter` in `.env` to use the original
OpenRouter `text-embedding-3-large` store). Judge embeddings: `all-minilm`.

## Run

```bat
python -m evals.01_component_level.eval_retriever
python -m evals.01_component_level.eval_generator
python -m evals.02_pipeline.eval_rag_pipeline
python -m evals.03_application.eval_application
python -m evals.03_application.eval_citation
python -m evals.04_safety.eval_toxicity
python -m evals.04_safety.eval_leakage
python -m evals.04_safety.eval_scope
python -m evals.04_safety.eval_indirect_injection
python -m evals.05_operations.eval_ops
python -m evals.08_agent.eval_agent
python -m evals.07_online.simulate_traffic --n 20
python -m evals.07_online.online_eval
python -m evals.09_model_selection.eval_model_selection --models gpt-oss:20b-cloud gpt-oss:120b-cloud
```

Every eval writes per-case details (answers, scores, judge reasons) to `experiments/<eval>_<timestamp>.csv`.

### Regression gate

```bat
:: once, after a good run
python -m evals.06_regression.run_suite --suite all --no-run --set-baseline

:: after every change (prompt, model, chunking, top_k)
python -m evals.06_regression.run_suite
```

Exits with code 1 if any metric drops more than 0.05 below baseline (or p95 latency rises >20%),
printing which config changed. `.github/workflows/evals.yml` runs this gate on pull requests.

### DeepEval vs RAGAS

```bat
python compare_frameworks.py
```

---

## Project layout

```
src/                 RAG app (retriever, reranker, generator, pipeline) + support agent (agent, mock store)
goldens/             golden datasets (RAG, safety, agent, Text-to-SQL)
judge.py             shared RAGAS judge (Ollama gpt-oss) + embeddings
harness.py           dataset building, safe scoring, summaries
safety_judges.py     shared safety judges + programmatic leak detectors
evals/01..09         one folder per evaluation level
regression/          baseline + versioned run snapshots
```
