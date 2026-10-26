"""
LangGraph agent with tools — tracing automatic.

Graph:
    START -> agent --(tool call?)--> tools -> agent -> ... -> END
"""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from langchain_core.messages import HumanMessage, SystemMessage  # noqa: E402
# ---------------------------------------------------------
# HumanMessage / SystemMessage  (langchain_core) -- chat messages ki classes
#   HumanMessage(content=...) = user, SystemMessage(content=...) = instructions.
# ---------------------------------------------------------
from langchain_core.tools import tool  # noqa: E402
# ---------------------------------------------------------
# tool  (decorator, langchain_core) -- Python function ko LLM TOOL bana deta ha
#   Function ka naam + docstring + type hints = tool ki description/schema.
#   LangSmith ma har tool call ek "tool" run dikhta ha (input + output).
# ---------------------------------------------------------
from langchain_groq import ChatGroq  # noqa: E402
# ---------------------------------------------------------
# ChatGroq  (class, langchain-groq) -- Groq ka LangChain chat model
#   LangChain ke andar Groq LLM: chain = prompt | ChatGroq(...) | parser.
#   LangChain runs LangSmith ma KHUD trace hote hain (env vars set hon to).
#   Attributes (constructor):
#     model            -> Groq model id (llama-3.3-70b-versatile, openai/gpt-oss-120b...)
#     temperature      -> 0 = sab se consistent jawab
#     max_tokens       -> jawab ki max lambai (None = model ka default)
#     reasoning_effort -> sirf reasoning models (gpt-oss): "low" | "medium" | "high"
#     reasoning_format -> "parsed" | "raw" | "hidden" -- reasoning kaise wapas aaye
#     timeout, max_retries -> network settings
#     api_key          -> na do to GROQ_API_KEY env var se
#   Methods: .invoke(), .stream(), .bind_tools([...]) (tool calling),
#            .with_structured_output(Schema) (JSON / pydantic output)
# ---------------------------------------------------------
from langgraph.graph import END, START, MessagesState, StateGraph  # noqa: E402
# ---------------------------------------------------------
# langgraph.graph -- agent ka graph banane ke liye
#   StateGraph(MessagesState) -> graph jiski state = messages ki list
#   START / END               -> graph ka shuru aur aakhri node
#   builder.add_node / add_edge / add_conditional_edges -> nodes aur raaste
#   builder.compile()         -> chalne wala graph (har node trace ma alag run)
# ---------------------------------------------------------
from langgraph.prebuilt import ToolNode, tools_condition  # noqa: E402
# ---------------------------------------------------------
# langgraph.prebuilt
#   ToolNode(tools)   -> LLM ne jo tool calls maangi, unhe chalane wala node
#   tools_condition   -> agar LLM ne tool maanga to "tools" node, warna END
# ---------------------------------------------------------

MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")  # tool calling support karta ha

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
llm = ChatGroq(model=MODEL, temperature=0).bind_tools(tools)

SYSTEM = SystemMessage(content="You are a watch store support agent. Use tools when needed.")


def agent_node(state: MessagesState) -> dict:
    response = llm.invoke([SYSTEM] + state["messages"])
    return {"messages": [response]}


builder = StateGraph(MessagesState)
builder.add_node("agent", agent_node)
builder.add_node("tools", ToolNode(tools))
builder.add_edge(START, "agent")
builder.add_conditional_edges("agent", tools_condition)  # tool call hai to "tools", warna END
builder.add_edge("tools", "agent")
graph = builder.compile()


if __name__ == "__main__":
    result = graph.invoke(
        {"messages": [HumanMessage(content="ORD-1001 ka status kya hai aur black chrono stock mein hai?")]},
        config={
            "run_name": "Support Agent",
            "tags": ["langgraph", "agent"],
            "metadata": {"user_id": "user_789", "thread_id": "conv-001"},
        },
    )
    print(result["messages"][-1].content)
    print("\nUI: trace mein agent -> tools -> agent loop dekho, har tool call ka input/output.")
