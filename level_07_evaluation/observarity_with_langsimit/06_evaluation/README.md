# 06 — Evaluation (Experiments)

## Concept
```
Dataset (examples)  ──>  Target function (tumhari app)  ──>  Outputs
                                                               │
                         Evaluators (score karte hain)  <──────┘
                                    │
                                    v
                         Experiment (results + scores LangSmith mein)
```

- **Target**: `def target(inputs: dict) -> dict` — dataset ka input lo, app chalao, output do
- **Evaluator**: `def my_eval(inputs, outputs, reference_outputs) -> bool | float | dict`
  - Sirf jo arguments chahiye wo likho (e.g. sirf `outputs`)
  - `example` / `run` bhi le sakte ho (metadata wagera ke liye)
- **Summary evaluator**: poore experiment par ek score (e.g. pass rate)
- **Experiment**: ek eval run. Do experiments ko UI mein **side-by-side compare** karte hain

## Evaluators ki 3 qismein
| Type | Kab | Example |
|---|---|---|
| **Code / heuristic** | Rule se check ho sakta hai | length, JSON valid, keyword mojood, regex |
| **LLM-as-judge** | Meaning check karna hai | correctness, helpfulness, tone, hallucination |
| **Human** | Sabse accurate, mehnga | Annotation queues (UI) |

## Files (pehle `05_datasets/01_create_dataset.py` chala lo)
| File | Concept |
|---|---|
| `support_app.py` | Jis app ko test kar rahe hain (2 prompt versions: v1, v2) |
| `01_code_evaluators.py` | Simple code evaluators + `client.evaluate` + results pandas mein |
| `02_llm_as_judge.py` | `openevals` ka ready judge + apna custom judge |
| `03_compare_experiments.py` | Prompt v1 vs v2 — summary evaluators ke saath, phir UI mein compare |
| `pytest_evals/` | CI/CD ke liye evals — pytest se chalte hain |

```powershell
python 06_evaluation\01_code_evaluators.py
python 06_evaluation\02_llm_as_judge.py
python 06_evaluation\03_compare_experiments.py
pytest 06_evaluation\pytest_evals -v
```

## UI
Datasets & Experiments → `watch-support-qa` → **Experiments** tab
→ do experiments select karo → **Compare** → kaunse examples par score gira/bara.
