# 08 — Scores, Feedback & Monitoring

## Concept: Scores
Langfuse mein har qism ki "quality value" ek **score** hai — chahe kahin se aaye:
| Source | Example |
|---|---|
| User | 👍/👎 (`user_rating`), stars |
| Code / evaluator | `concise = 1`, `has_context = 0` |
| LLM-as-a-Judge (UI) | `helpfulness = 0.8` |
| Human (annotation queue) | `correct = 1`, reason = `wrong_info` |

Score kis par lag sakta hai: **trace**, **observation**, ya **session** (poori conversation).

Data types: `NUMERIC` (float), `BOOLEAN` (1/0), `CATEGORICAL` (string), `TEXT`.

## Feedback ke liye trace_id chahiye
```python
@observe()
def handle(q):
    ...
    return {"answer": ..., "trace_id": langfuse.get_current_trace_id()}
# user click kare ->
langfuse.create_score(trace_id=..., name="user_rating", value=1, data_type="BOOLEAN")
```

## Files
| File | Concept |
|---|---|
| `01_user_feedback_scores.py` | trace_id wapas bhejna, boolean/numeric/categorical scores, code se score_current_trace, session score |
| `02_query_and_metrics.py` | Observations API + Metrics API se report: error rate, latency, cost per model, negative feedback |
| `03_ui_features_guide.md` | UI-only: LLM-as-a-Judge, annotation queues, dashboards, score configs, playground, model prices |

## Feedback loop (industry)
```
User 👎 -> create_score(user_rating=0) -> Traces filter: user_rating = 0
       -> Annotation queue (human review) -> Dataset item -> Prompt fix (folder 07)
       -> Experiment (folder 06) -> production label move
```
