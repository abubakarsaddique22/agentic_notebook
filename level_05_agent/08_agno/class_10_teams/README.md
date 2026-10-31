# Class 10 — Teams (Multi-Agent)

| File | Concept |
|---|---|
| `01_coordinate_mode.py` | **coordinate** — leader kaam baant ke final jawab khud likhta hai (default) |
| `02_route_mode.py` | **route** — leader sahi member ko bhejta hai, member ka jawab seedha user ko |
| `03_broadcast_mode.py` | **broadcast** — sab members ko same sawal, leader raaye milata hai |
| `04_tasks_mode.py` | **tasks** — leader task list bana ke loop mein complete karwata hai |
| `05_team_shared_state.py` | Team ka **shared session_state** + db + history |

## Kaunsa mode kab
| Mode | Kab | Cost |
|---|---|---|
| `route` | Sirf sahi specialist chahiye (support, language) | Sab se kam |
| `coordinate` | Kaam ke hisse alag members karein, ek final jawab | Medium |
| `broadcast` | Alag nazariye / verification | Zyada |
| `tasks` | Bara open-ended goal | Sab se zyada |

## Yaad rakho
- Member ka **`role`** saaf likho — leader isi se faisla karta hai.
- `show_members_responses=True` → debugging mein members ke jawab dekho.
- `team.cli_app()` → terminal mein chat.

## Run
```
uv run python class_10_teams\01_coordinate_mode.py
uv run python class_10_teams\02_route_mode.py
uv run python class_10_teams\03_broadcast_mode.py
uv run python class_10_teams\04_tasks_mode.py
uv run python class_10_teams\05_team_shared_state.py
```
