# 06 — Evaluation (Experiments)

## Concept
```
Data (local list YA Langfuse dataset)  ──>  task(item)  ──>  output
                                                              │
                        evaluators(input, output, expected) <─┘   -> per-item scores
                        run_evaluators(item_results)              -> poore run ka ek score
                                     │
                                     v
                       Experiment / Dataset Run  (Langfuse UI mein, compare kar sakte ho)
```

## Signatures (yaad kar lo)
```python
from langfuse import Evaluation, get_client

def task(*, item, **kwargs):                 # local data: item["input"]  | dataset: item.input
    return my_app(...)

def my_eval(*, input, output, expected_output, metadata, **kwargs):
    return Evaluation(name="concise", value=1, comment="...")    # ya list[Evaluation], ya [] (skip)

def my_run_eval(*, item_results, **kwargs):  # summary evaluator
    return Evaluation(name="pass_rate", value=0.9)

result = langfuse.run_experiment(name=..., data=[...], task=task, evaluators=[...], run_evaluators=[...])
result = dataset.run_experiment(name=..., run_name=..., task=task, evaluators=[...])
print(result.format())
```

## LangSmith se farq
| LangSmith | Langfuse |
|---|---|
| `client.evaluate(target, data=...)` | `dataset.run_experiment(task=...)` / `langfuse.run_experiment(data=...)` |
| `target(inputs)` | `task(*, item, **kwargs)` |
| evaluator returns bool/dict | evaluator returns `Evaluation(...)` |
| `summary_evaluators` | `run_evaluators` |
| `experiment_prefix` | `name` + `run_name` |
| `openevals` | `autoevals` (adapter: `create_evaluator_from_autoevals`) + UI ke LLM-as-a-Judge |

## Files (pehle `05_datasets/01_create_dataset.py` chala lo)
| File | Concept |
|---|---|
| `support_app.py` | Jis bot ko test kar rahe hain (prompt v1 aur v2) |
| `01_local_experiment.py` | Dataset ke bina — local list par jaldi experiment |
| `02_dataset_experiment.py` | Langfuse dataset par experiment + code evaluators + run evaluator + split filter |
| `03_llm_as_judge.py` | Apna LLM judge (multiple scores) + autoevals `Factuality` |
| `04_compare_prompt_versions.py` | v1 vs v2 — phir UI mein compare |
| `pytest_evals/` | CI/CD gate — fail ho to deploy ruk jaye |

```powershell
python 06_evaluation\01_local_experiment.py
python 06_evaluation\02_dataset_experiment.py
python 06_evaluation\03_llm_as_judge.py
python 06_evaluation\04_compare_prompt_versions.py
pytest 06_evaluation\pytest_evals -v -s
```

## UI
Datasets → `watch-support-qa` → **Runs** tab → 2 runs select → **Compare** → item-wise outputs + scores.
Experiment traces ka environment `sdk-experiment` hota hai (production traces se alag rehte hain).
