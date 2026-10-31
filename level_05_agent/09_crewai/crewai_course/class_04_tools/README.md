# Class 04 — Tools

| File | Concept |
|---|---|
| `01_builtin_tools.py` | **Built-in tools** (`crewai_tools`): DirectoryRead, FileRead, FileWriter, SerperDev |
| `02_custom_tool_decorator.py` | **Custom tool — `@tool` decorator** (asaan tareeqa) |
| `03_custom_tool_class.py` | **Custom tool — `BaseTool` class** + `args_schema`, caching, `result_as_answer` |
| `sample_data/` | Practice ke liye fake store data |

## Tool kaise kaam karta hai
1. Agent ko tools ki list milti hai (naam + description).
2. Agent sochta hai: "is sawal ke liye mujhe kaunsa tool chahiye?"
3. Tool call karta hai → result parhta hai → final jawab deta hai.

**Isliye tool ki description sab se important hai.** Wahi agent ka "instruction manual" hai.

## @tool vs BaseTool
| | `@tool` | `BaseTool` |
|---|---|---|
| Likhna | Bahut asaan | Thora lamba |
| Input validation | Type hints | Pydantic `args_schema` (strict) |
| Settings/state rakhna | Mushkil | Asaan (class fields) |

## Run
```
uv run python class_04_tools\01_builtin_tools.py
uv run python class_04_tools\02_custom_tool_decorator.py
uv run python class_04_tools\03_custom_tool_class.py
```
Web search ke liye `.env` mein `SERPER_API_KEY` daalo (optional — iske baghair bhi file 01 chalti hai).
