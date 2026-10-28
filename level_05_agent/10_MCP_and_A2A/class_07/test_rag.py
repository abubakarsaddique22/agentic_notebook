"""Test real vector-based policy retrieval without calling Groq."""
import asyncio
from mcp import Client

async def main():
    async with Client("http://127.0.0.1:8002/mcp") as client:
        tools = await client.list_tools()
        print("Policy tools:", [t.name for t in tools.tools])
        for question in [
            "Can I fly business class for a short flight?",
            "What hotel star rating and nightly budget are allowed?",
            "Which receipts are needed for reimbursement?",
        ]:
            result = await client.call_tool("search_company_policy", {"query": question, "top_k": 2})
            if result.is_error:
                raise RuntimeError(str(result.content))
            print("\nQUESTION:", question)
            print("RESULT:", result.structured_content or [x.text for x in result.content if hasattr(x, "text")])

if __name__ == "__main__":
    asyncio.run(main())
