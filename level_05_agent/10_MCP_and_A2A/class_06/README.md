# Class 06 — Multiple MCP Servers + One Groq LangChain Agent

**Roman Urdu practical notes | Python 3.11+ | Streamable HTTP**

## Objective

Class 5 ke Travel MCP ko preserve karke Policy MCP aur Work MCP add karna, phir ek LangChain agent se teeno servers ke tools call karwana.

```text
User → Groq LLM + LangChain Agent → MCPAdapter
                                     ├── Travel MCP  :8001 (weather, flight, budget)
                                     ├── Policy MCP  :8002 (policy search)
                                     └── Work MCP    :8003 (demo tasks)
```

## Files

- `servers/travel_server.py`: Class 5 ka real Open-Meteo current-weather tool; sample flight tool; budget tool; fixed travel preferences, city template aur planning prompt.
- `servers/policy_server.py`: Fixed example policies + keyword search tool. **Abhi semantic RAG nahi hai**, wo Class 7 mein hoga.
- `servers/work_server.py`: In-memory task creation aur list. Server restart par tasks delete ho jaate hain. No Jira/Linear integration.
- `test_connections.py`: Teeno servers ki discovery test.
- `start_servers.py`: Teeno server processes ek terminal se run/stop karne ka optional shortcut.
- `agent.py`: HTTP MCP context retrieval, MCPAdapter, Groq LLM, LangChain agent, message trace.

## Setup — Windows PowerShell

Project root `MCP_Practical` mein environment aur `.env` ho:

```powershell
.venv\Scripts\Activate.ps1
cd class_06
python -m pip install -r requirements.txt
```

Project root ki `.env` file:

```dotenv
GROQ_API_KEY=your_real_groq_key
```

## Run servers

**Option A:** Three terminals, each in `class_06` directory:

```powershell
python servers/travel_server.py
python servers/policy_server.py
python servers/work_server.py
```

Har command **alag terminal** mein. URLs: `http://127.0.0.1:8001/mcp`, `http://127.0.0.1:8002/mcp`, `http://127.0.0.1:8003/mcp`.

**Option B:** One terminal in class_06:

```powershell
python start_servers.py
```

Option A aur B dono ek saath use mat karo. Class 5 ka server 8001 par running ho to pehle Ctrl+C se stop karo.

## Verify connections

Fourth terminal mein:

```powershell
python test_connections.py
```

Expected tool lists:

```text
Travel: search_flights, calculate_budget, get_live_weather
Policy: search_company_policy
Work: create_trip_task, list_trip_tasks
```

## Run the Groq Agent

```powershell
python agent.py
```

Agent user ki Lahore to Dubai trip request leta hai: real current weather, example flight, example travel policy, example budget, one demo task. `MCPAdapter` teeno endpoints se tools discover karke names prefix karta hai:

```text
travel_search_flights
travel_calculate_budget
travel_get_live_weather
policy_search_company_policy
work_create_trip_task
work_list_trip_tasks
```

`agent.py` ka key config:

```python
config = {'mcpServers': {
  'travel': {'url': 'http://127.0.0.1:8001/mcp'},
  'policy': {'url': 'http://127.0.0.1:8002/mcp'},
  'work': {'url': 'http://127.0.0.1:8003/mcp'},
}}
async with MCPAdapter(config) as adapter:
    tools = await adapter.list_tools()
```

**Concept:** MCPAdapter tool schemas ko LangChain format mein map karta hai. Prefix (`travel_`, `policy_`, `work_`) tool routing/collision avoidance ke liye hai. Agent ko ek tools list milti hai; woh user intent ke mutabiq select karta hai.

## Resource/Prompt integration

`agent.py` ka `load_context()` manually `travel://preferences`, `city://Dubai/guide`, `policy://travel-summary` aur `plan_business_trip` fetch karta hai. **Resources/Prompts LLM mein automatically inject nahi hote.** Hum explicit system prompt mein add karte hain.

## Limitations & safety

- Weather Open-Meteo ka real data hai, network required.
- Flight tool **demo** data deta hai: live flight/booking nahi.
- Policy examples real company ki policies nahi, aur policy hotel limit INR mein jabke demo budget PKR mein hai. Currency conversion ke baghair compare mat karo.
- Work tasks in-memory demo hain; restart par lost.
- Model ke calls/order deterministic nahi; `MESSAGE FLOW` se actual verify karo.
- Production mein HTTPS, auth, approvals for side effects, secrets management, persistent DB aur monitoring add karo.

## Practice

1. `test_connections.py` se teeno server tools discover karo.
2. Policy server mein `visa` policy add karo.
3. Demo task create karwao, phir tasks list check karo.
4. Agent destination Dubai se London change karo (question/context dono).
5. Ek server band karke exception/failure observe karo.

## Troubleshooting

- `Connection refused`: teen servers running hon.
- `Address already in use`: old Class 5 server ya duplicate launcher stop karo.
- `GROQ_API_KEY missing`: `.env` project root mein check karo.
- `ModuleNotFoundError`: venv activate + requirements install.
- Weather error: Open-Meteo/internet check karo; model ko fabricated weather dene mat do.

## Next

Class 7 mein `search_company_policy` ko embeddings + vector semantic retrieval (RAG) se upgrade karenge.

Official refs: https://py.sdk.modelcontextprotocol.io/run/ and https://github.com/langchain-ai/langchain/blob/master/openwiki/mcp-integration.md
