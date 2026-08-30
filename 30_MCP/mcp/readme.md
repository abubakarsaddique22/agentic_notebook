# Architecture
```
                         ┌─────────────────────┐
                         │     client.py       │
                         │                     │
                         │    LangGraph + LLM  │
                         └──────────┬──────────┘
                                    │
                         MultiServerMCPClient
                                    │
              ┌─────────────────────┼
              │                     │                     
              ▼                     ▼                     
     ┌────────────────┐    ┌────────────────┐    
     │  Local MCP     │    │ Tavily Remote  │   
     │    Server      │    │      MCP       │   
     │                │    │                │  
     │  server.py     │    │ mcp.tavily.com │   
     │                │    │                │    
     │ my tools       │    │ web search     │   
     └────────────────┘    └────────────────┘   
```

And importantly:

You do NOT need to write the Tavily server yourself.

Tavily already hosts it.


# MCP Multi-Server Agent

A practice project using **MCP + LangGraph + Groq** to connect multiple MCP servers with one AI agent.

## Architecture

```text
                    User
                     │
                     ▼
                 client.py
                     │
          ┌──────────┴──────────┐
          ▼                     ▼
    Local MCP Server        Tavily MCP
       (stdio)           (Streamable HTTP)
          │                     │
          └──────────┬──────────┘
                     ▼
               MCP Tools
                     │
                     ▼
                Groq LLM
                     │
                     ▼
                LangGraph
                ┌───────┐
                │ Chat  │
                └───┬───┘
                    │
              Tool required?
               /          \
             Yes           No
              │             │
              ▼             ▼
           Tools           END
              │
              └──────► Chat
```

## Project Structure

```text
mcp_practice/
├── client.py
├── local_server.py
├── .env
├── .gitignore
└── README.md
```

## How It Works

1. `client.py` connects to Local MCP and Tavily MCP.
2. `get_tools()` discovers tools from both servers.
3. Tools are provided to the Groq LLM.
4. LangGraph decides whether a tool is required.
5. `ToolNode` executes the selected MCP tool.
6. The result goes back to the LLM for the final answer.

## MCP Transports

* **Local MCP:** `stdio`
* **Tavily MCP:** `Streamable HTTP`
* **Tavily authentication:** API key through `.env`

## Future

Google Drive and Gmail MCP servers can be added using **OAuth authentication**.
