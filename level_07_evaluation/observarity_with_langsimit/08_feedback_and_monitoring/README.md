# 08 — Feedback & Monitoring

## Concepts
- **Feedback**: kisi run par score/comment attach karna. Source ho sakta hai:
  user (thumbs up/down), human reviewer, ya automatic evaluator.
- **run_id**: feedback dene ke liye run ki ID chahiye → isliye run_id **khud generate** karke pass karte hain.
- **Monitoring**: production runs ko query karke error rate, latency, cost nikalna (code se ya UI dashboards se).

## Files
| File | Concept |
|---|---|
| `01_user_feedback.py` | run_id control karna, thumbs up/down, correction, presigned feedback URL |
| `02_query_runs_analytics.py` | Runs query → error rate, p50/p95 latency, tokens, cost, negative-feedback runs |
| `03_ui_features_guide.md` | UI-only features: online evaluators, automation rules, annotation queues, alerts, dashboards |

## Feedback loop (industry)
```
User 👎  ->  create_feedback(score=0)  ->  Automation rule: score=0 wale runs
         ->  Annotation queue (human review)  ->  Dataset mein add  ->  Prompt fix
         ->  Experiment (folder 06)  ->  Deploy
```
