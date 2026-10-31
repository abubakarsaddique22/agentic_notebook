# Class 02 — Tools

| File | Concept |
|---|---|
| `01_builtin_tools.py` | **Built-in toolkits**: DuckDuckGo, HackerNews, Calculator |
| `02_custom_function_tools.py` | **Python function = tool** (docstring + type hints) |
| `03_tool_decorator_toolkit.py` | **`@tool` options** (`show_result`, `stop_after_tool_call`, `cache_results`), **Toolkit class**, `tool_call_limit` |

## Tool kaise chalta hai
1. Model ko tools ki list milti hai (naam + docstring + parameters).
2. Model faisla karta hai: "mujhe `check_stock` chahiye".
3. Agno function chalata hai → result model ko wapas.
4. Model final jawab banata hai.

## Tips
- Docstring saaf likho — wahi model ka "manual" hai.
- Tool hamesha **string** return kare.
- `tool_call_limit` lagao — kharcha aur loops control.

## Run
```
uv run python class_02_tools\01_builtin_tools.py
uv run python class_02_tools\02_custom_function_tools.py
uv run python class_02_tools\03_tool_decorator_toolkit.py
```
