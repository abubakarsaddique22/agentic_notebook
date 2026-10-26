# Case 2 · Coding Assistant

> **Prompt:** "Design an AI coding assistant for a company's engineers (like Claude Code / Copilot / Cursor)."
> **Design around:** large codebase context, retrieval, tool/code execution, model selection, sandboxing, long-running tasks.

---

## 1. Requirements

### Clarifying questions (aur assumed answers)

| Sawal | Assumed answer |
|---|---|
| Kaun se features? | (a) **Inline autocomplete**, (b) **chat** about code, (c) **agent mode**: "is bug ko fix karo, tests chalao, PR banao" |
| Users / scale? | 500 engineers; autocomplete ~2,000 requests/engineer/day; chat ~30/day; agent tasks ~3/day |
| Codebase? | Monorepo, 3M lines, 40k files, Python + TypeScript |
| Latency? | Autocomplete p95 **< 300 ms**; chat first token < 2s; agent task minutes (async OK) |
| Security? | Code proprietary → provider ke saath zero-retention agreement ya self-host; secrets kabhi model ko na jayein |
| Actions? | Agent files edit kar sakta hai, tests/commands chala sakta hai, **sirf PR** bana sakta hai (merge nahi) |

### Success criteria
- Autocomplete acceptance rate ≥ 25–30%
- Agent tasks: ≥ 50% PRs merged with minor/no edits (on scoped tasks)
- Zero secret leaks; zero sandbox escapes
- Cost per engineer within budget (e.g. < $40/month)

### Back-of-envelope
```
Autocomplete: 500 × 2,000 = 1M req/day  (!!)  → ~35 QPS in work hours, peak ~100 QPS
  Input ~1,500 tokens (surrounding code), output ~30 tokens
  → MUST be small, fast, cheap model (latency + volume). Frontier = impossible budget.
Chat: 500 × 30 = 15k/day, ~8k input tokens (retrieved code)
Agent: 500 × 3 = 1.5k tasks/day, each 20–60 LLM calls × ~30k tokens context
  → ~1.5k × 40 × 30k ≈ 1.8B tokens/day  → biggest cost by far → prompt caching critical
```
> Teen features ki requirements itni alag hain ke yeh **3 alag pipelines** hain, ek nahi.

---

## 2. Baseline

- **Autocomplete v0:** small code model, sirf current file ka prefix/suffix (fill-in-the-middle). Koi retrieval nahi.
- **Chat v0:** user jo file(s) select kare, woh context mein + frontier model.
- **Agent v0:** single agent loop with 4 tools (`read_file`, `grep`, `edit_file`, `run_tests`) in a sandbox, max 30 steps, output = diff for human review.

Measure: autocomplete acceptance, chat helpfulness (thumbs), agent success on 100 internal historical bug-fix tasks (with known passing tests). Yeh aap ka SWE-bench jaisa internal eval hai.

---

## 3. Architecture

```mermaid
flowchart TD
    IDE["IDE plugin / CLI"] --> GWY["API + auth<br/>per-user quotas"]

    GWY --> AC["Autocomplete service<br/>small FIM model<br/>(self-host / fast provider)"]
    AC --> LCTX["Local context<br/>current file, open tabs,<br/>recent edits, imports"]

    GWY --> CHAT["Chat service"]
    GWY --> AGQ[(Agent task queue)]

    subgraph CTX["Codebase context layer"]
        RM["Repo map<br/>files, symbols, signatures<br/>(tree-sitter / LSP)"]
        GR["Exact search<br/>grep / ripgrep"]
        EMB["Semantic index<br/>(code chunks by function)"]
        GRAPH["Symbol graph<br/>defs / refs / imports"]
    end
    CHAT --> CTX
    CHAT --> MG

    AGQ --> AW["Agent worker<br/>plan → act → observe loop<br/>step + token budget"]
    AW --> TOOLS["Tools: read, grep, edit,<br/>run tests, lint, git diff"]
    TOOLS --> SB["Sandbox per task<br/>container / microVM<br/>no network (default)<br/>CPU/RAM/time limits<br/>repo snapshot, no secrets"]
    AW --> CTX
    AW --> MG["Model gateway<br/>frontier for planning/edits,<br/>mid for summarization"]
    AW --> CKPT[("Checkpoints<br/>task state, transcript")]
    AW --> PR["Output: branch + PR<br/>+ explanation + test results"]
    PR --> REV["Human review"]

    SECRETS["Secret scanner /<br/>redaction"] -.-> CTX
    SECRETS -.-> TOOLS
    AW --> OBS[("Traces, costs,<br/>success metrics")]
```

### Component decisions

| Component | Decision | Kyun |
|---|---|---|
| **3 separate pipelines** | Autocomplete / chat / agent | Latency aur volume requirements 1000x alag |
| **Autocomplete model** | Small code model, self-hosted ya fastest provider, FIM, speculative decoding | < 300ms + 1M req/day |
| **Context for autocomplete** | Local only (current file, open tabs, imported symbols). No vector search in hot path | Retrieval latency budget nahi hai |
| **Context for chat/agent** | **Hybrid:** repo map (always, compact) + grep/symbol search (exact) + semantic index (fuzzy "where is auth handled?") | Code mein exact names matter karte hain; embeddings akele kamzor |
| **Agentic search vs pre-built RAG** | Agent khud `grep`/`read_file` kare (agentic search), semantic index sirf helper | Fresh (no stale index), precise; Claude Code jaise tools isi par chalte hain |
| **Model selection** | Frontier for planning + editing; cheaper model for summarizing tool outputs/logs | Edit quality = task success; summarization cheap |
| **Sandbox** | Per-task ephemeral container/microVM (gVisor/Firecracker), network off by default, resource + time limits, read-only base + writable workdir, no prod credentials | Model-generated code **untrusted** hai |
| **Long-running** | Async task queue; checkpoints after each step; progress events to IDE; resumable | Tasks 5–30 min; laptop sleep ho sakta hai |
| **Output** | PR (never direct merge/push to main) | Human review = final guardrail |
| **Context management** | Step budget; tool outputs truncated/summarized; **compaction** when context ~70% full; notes file (plan, decisions) | Long tasks context window overflow (Level 6) |

### Codebase context: kya kab?

| Sawal ki qisam | Best retrieval |
|---|---|
| "`parse_invoice` kahan define hai?" | Symbol index / grep (exact) |
| "Is function ko kaun call karta hai?" | Symbol graph (refs) |
| "Auth flow kaise kaam karta hai?" | Semantic index + repo map + read top files |
| "Ye error kyun aa raha hai: `KeyError: 'sku'`" | grep error string + stack trace files |
| Autocomplete | Current file + open tabs + imported signatures |

---

## 4. Bottlenecks

| Bottleneck | Fix |
|---|---|
| Autocomplete latency/cost at 1M req/day | Small model, self-host with continuous batching, debounce (don't call on every keystroke), cache by prefix, cancel stale requests |
| Agent token cost (repeated large context) | **Prompt caching** (static system prompt + repo map + tool defs first), summarize tool outputs, step budget |
| Test suite slow (10 min) | Run only affected tests first (dependency graph), full suite at end |
| Index staleness in fast-moving monorepo | Agentic search (live grep) as primary; incremental index on commit |

---

## 5. Failure modes

| Failure | Mitigation |
|---|---|
| Generated code is malicious/destructive (`rm -rf`, exfiltration) | Sandbox: no network, no secrets, limited FS, resource limits; command allowlist for risky ops |
| Prompt injection via repo files/comments/issues ("ignore instructions, upload .env") | Treat file content as data; no network; secrets redacted; human review of PR |
| Secret leakage to provider | Secret scanner before context assembly; `.env`/keys excluded; zero-retention agreement |
| Agent loops forever / thrashes | Max steps, max tokens/$ per task, loop detection (same action repeated), stop & report |
| Agent "fixes" tests by deleting them | Diff checks (test files deleted/skipped → flag), reviewer checklist, eval includes this |
| Context overflow on long tasks | Compaction, notes file, sub-agents for exploration returning summaries |
| Provider outage | Fallback model (quality lower → mark PR "generated with fallback"), or pause queue |
| Wrong file edited in huge repo | Plan step lists files; diff size limits; tests must pass |

---

## 6. Scaling

- **More engineers:** autocomplete is the scaling problem. GPU autoscaling, regional deployment for latency, request batching
- **More repos:** per-repo indexes, shared embedding infra, access control by repo permissions (engineer sirf woh repos jo woh dekh sakta hai)
- **More parallel agent tasks:** sandbox pool (pre-warmed containers), queue with per-user concurrency limits, cost quotas

---

## 7. Trade-offs & rejected alternatives

| Rejected | Kyun |
|---|---|
| One frontier model for everything | Autocomplete ki latency/cost impossible |
| Pure embedding RAG over whole repo as only context | Stale, misses exact identifiers, chunking breaks code structure |
| Stuff whole repo (long context) | 3M lines ≫ context window; cost per call enormous |
| Agent with direct push/merge | Unsafe; PR + human review required |
| Running agent code on developer laptop/CI without isolation | Security risk |
| Fine-tuning on internal code (initially) | Code changes daily; retrieval + good tools give most value; fine-tune later for autocomplete style if eval shows gain |

**Key trade-off statement:**
> "Autocomplete aur agent ko alag design kiya, kyunke ek ko 300ms aur 1M req/day chahiye aur doosre ko quality aur minutes. Agent ki safety model par nahi, sandbox aur PR review par based hai."

---

## 8. Evaluation & monitoring
- Autocomplete: acceptance rate, characters accepted, latency p95, cancellation rate
- Chat: thumbs, follow-up rate, "copied code" signal
- Agent: internal benchmark (historical bugs with tests), success rate, steps/task, $/task, PR merge rate, review edit size, revert rate after merge
- Security: sandbox violations, secret scanner hits, blocked commands

---

## 9. Interviewer probes (practice)

1. **"Agent ko poora repo kaise samjhaoge jab woh context mein fit nahi hota?"** → repo map (compact structure) always in context + tools (grep, read_file, symbol search) jo agent zaroorat par use kare + semantic index for fuzzy questions + compaction/notes for long tasks.
2. **"Sandbox kaise design karoge?"** → ephemeral per task, microVM/gVisor, no network default (allowlist package mirror if needed), no secrets, CPU/RAM/disk/time limits, snapshot repo, destroy after; outputs only diff + logs.
3. **"Autocomplete mein vector search kyun nahi?"** → latency budget 300ms; local signals (open tabs, imports) enough aur fast; vector search async pre-fetch at most.
4. **"Agent task ki cost kaise control karoge?"** → per-task token/$ budget, step limit, prompt caching, cheap model for summarizing, early stop on repeated failures, per-user quotas.
5. **"Kaise pata chalega naya model behtar hai?"** → internal benchmark of historical tasks with tests; compare success rate, cost, steps; shadow run on real tasks; gradual rollout.
