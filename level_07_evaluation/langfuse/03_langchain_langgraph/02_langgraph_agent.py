"""
LangGraph agent with tools — Langfuse CallbackHandler se trace.

Graph:
    START -> agent --(tool call?)--> tools -> agent -> ... -> END
"""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from langchain_core.messages import HumanMessage, SystemMessage  # noqa: E402
from langchain_core.tools import tool  # noqa: E402
from langchain_openai import ChatOpenAI  # noqa: E402
from langfuse import get_client  # noqa: E402
from langfuse.langchain import CallbackHandler  # noqa: E402
from langgraph.graph import START, MessagesState, StateGraph  # noqa: E402
from langgraph.prebuilt import ToolNode, tools_condition  # noqa: E402

MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
langfuse = get_client()

ORDERS = {"ORD-1001": "shipped", "ORD-2002": "processing"}
STOCK = {"black chrono": 4, "silver classic": 0}


@tool
def get_order_status(order_id: str) -> str:
    """Order ID se order ka status batata hai."""
    return ORDERS.get(order_id.upper(), "order not found")


@tool
def check_stock(product_name: str) -> str:
    """Product ka stock check karta hai."""
    qty = STOCK.get(product_name.lower())
    return "product not found" if qty is None else f"{qty} in stock"


tools = [get_order_status, check_stock]
llm = ChatOpenAI(model=MODEL, temperature=0).bind_tools(tools)
SYSTEM = SystemMessage(content="You are a watch store support agent. Use tools when needed.")


def agent_node(state: MessagesState) -> dict:
    return {"messages": [llm.invoke([SYSTEM] + state["messages"])]}


builder = StateGraph(MessagesState)
builder.add_node("agent", agent_node)
builder.add_node("tools", ToolNode(tools))
builder.add_edge(START, "agent")
builder.add_conditional_edges("agent", tools_condition)  # tool call -> "tools", warna END
builder.add_edge("tools", "agent")
graph = builder.compile()


if __name__ == "__main__":
    handler = CallbackHandler()
    result = graph.invoke(
        {"messages": [HumanMessage(content="ORD-1001 ka status kya hai aur black chrono stock mein hai?")]},
        config={
            "callbacks": [handler],
            "metadata": {
                "langfuse_user_id": "user_789",
                "langfuse_session_id": "conv-001",
                "langfuse_tags": ["langgraph", "agent"],
                "langfuse_trace_name": "support-agent",
            },
        },
    )
    print(result["messages"][-1].content)
    langfuse.flush()
    print("\nUI: trace kholo -> agent -> tools -> agent loop. Upar 'Agent Graph' view bhi dekho.")
