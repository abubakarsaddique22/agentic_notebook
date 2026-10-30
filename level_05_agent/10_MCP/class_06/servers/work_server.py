
from mcp.server import MCPServer

# 1. Create MCP Server
server = MCPServer("Work Management MCP Server")

# 2. Store demo tasks
TASKS = []


# =========================
# 3. MCP TOOLS
# =========================

@server.tool()
def create_trip_task(title: str, owner: str = "Travel Team") -> dict:
    """Create a demo trip task."""

    if not title.strip():
        return {
            "created": False,
            "error": "Title cannot be empty"
        }

    task = {
        "task_id": f"TRIP-{len(TASKS) + 101}",
        "title": title,
        "owner": owner,
        "status": "open"
    }

    TASKS.append(task)

    return {
        "created": True,
        "task": task,
        "demo": True
    }


@server.tool()
def list_trip_tasks() -> list:
    """Return all created demo tasks."""

    return TASKS


# =========================
# 4. RUN MCP SERVER
# =========================

if __name__ == "__main__":
    server.run(
        transport="streamable-http",
        host="127.0.0.1",
        port=8003,
        stateless_http=True,
        json_response=True
    )
