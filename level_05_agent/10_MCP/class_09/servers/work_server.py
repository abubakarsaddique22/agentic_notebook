from mcp.server import MCPServer

server = MCPServer('Work Management MCP Server')
TASKS = []  # Demo in-process storage; resets when server restarts.

@server.tool()
def create_trip_task(title: str, owner: str = 'Travel Team') -> dict:
    """Create a DEMO task in this server's memory; no external work system is updated."""
    if not title.strip():
        return {'created': False, 'error': 'Title cannot be empty'}
    task = {'task_id': f'TRIP-{len(TASKS) + 101}', 'title': title.strip(), 'owner': owner, 'status': 'open'}
    TASKS.append(task)
    return {'created': True, 'task': task, 'demo': True}

@server.tool()
def list_trip_tasks() -> list[dict]:
    """List demo in-memory tasks; the list resets after server restart."""
    return TASKS

if __name__ == '__main__':
    server.run(transport='streamable-http', host='0.0.0.0', port=8003, stateless_http=True, json_response=True)
