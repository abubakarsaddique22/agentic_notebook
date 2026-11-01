"""EASY VERSION: Work Management MCP server (port 8003). Tasks sirf memory mein rehte hain."""
from mcp.server import MCPServer

server = MCPServer("Work Management MCP Server")

# Saare tasks is list mein. Server band = list khali.
TASKS = []


# ============================================
# TOOL 1: NAYA TASK BANAO
# ============================================

@server.tool()
def create_trip_task(title: str, owner: str = "Travel Team") -> dict:
    """Create a DEMO task in this server's memory; no external work system is updated."""
    title = title.strip()

    if title == "":
        return {"created": False, "error": "Title cannot be empty"}

    # Pehla task TRIP-101, doosra TRIP-102, waghera
    task_id = f"TRIP-{len(TASKS) + 101}"

    task = {
        "task_id": task_id,
        "title": title,
        "owner": owner,
        "status": "open",
    }
    TASKS.append(task)

    return {"created": True, "task": task, "demo": True}


# ============================================
# TOOL 2: SAARE TASKS DIKHAO
# ============================================

@server.tool()
def list_trip_tasks() -> list[dict]:
    """List demo in-memory tasks; the list resets after server restart."""
    return TASKS


# ============================================
# RUN SERVER
# ============================================

if __name__ == "__main__":
    server.run(
        transport="streamable-http",
        host="127.0.0.1",
        port=8003,
        stateless_http=True,
        json_response=True,
    )