
from mcp.server import MCPServer

# 1. Create MCP Server
server = MCPServer("Company Policy MCP Server")


# 2. Demo Company Policies
POLICIES = {
    "flight": "Economy class required for trips under 8 hours. Business class needs director approval.",
    "hotel": "Maximum 4-star hotel. International hotel limit is 12000 INR per night.",
    "expense": "Flight, hotel and approved transport expenses are reimbursable with receipts."
}


# =========================
# 3. MCP TOOL
# =========================

@server.tool()
def search_company_policy(query: str) -> dict:
    """Search company policies using keywords."""

    matches = []

    for topic, policy in POLICIES.items():

        # Search keyword in topic or policy
        if query.lower() in topic.lower() or query.lower() in policy.lower():

            matches.append({
                "topic": topic,
                "text": policy
            })

    # If no match, return all demo policies
    if not matches:
        for topic, policy in POLICIES.items():
            matches.append({
                "topic": topic,
                "text": policy
            })

    return {
        "matches": matches,
        "demo": True
    }


# =========================
# 4. MCP RESOURCE
# =========================

@server.resource("policy://travel-summary")
def policy_summary() -> str:
    """Return all demo company policies."""

    return str(POLICIES)


# =========================
# 5. RUN MCP SERVER
# =========================

if __name__ == "__main__":
    server.run(
        transport="streamable-http",
        host="127.0.0.1",
        port=8002,
        stateless_http=True,
        json_response=True
    )
