import asyncio
import os
import sys

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, START
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from typing import TypedDict, Annotated


load_dotenv()


llm = ChatGroq(model="openai/gpt-oss-120b",temperature=0)


# ==================================================
# MCP CLIENT
# ==================================================

client = MultiServerMCPClient(

    {

        # ------------------------------------------
        # 1. YOUR LOCAL MCP SERVER
        # ------------------------------------------

        "local": {

            "transport": "stdio",
            "command": sys.executable,
            "args": ["local_server.py"],
        },

        # ------------------------------------------
        # 2. TAVILY REMOTE MCP SERVER
        # ------------------------------------------
        "tavily": {
            "transport": "streamable_http",
            "url": "https://mcp.tavily.com/mcp/",
            "headers": {
                "Authorization": f"Bearer {os.getenv('TAVILY_API_KEY')}"
            },
        },

       
    }
)



class State(TypedDict):
    messages: Annotated[list,add_messages]


async def build_graph():

    # ----------------------------------------------
    # Get tools from ALL MCP servers
    # ----------------------------------------------

    tools = await client.get_tools()


    print("\n==============================")
    print("AVAILABLE MCP TOOLS")
    print("==============================")

    for tool in tools:
        print(f"{tool.name}")

    # Give MCP tools to LLM
    llm_with_tools = llm.bind_tools(tools)


    
    # LLM NODE
    async def chat_node(state: State):

        response = await llm_with_tools.ainvoke(state["messages"])

        return {"messages": [response]}


    # TOOL NODE
    tool_node = ToolNode(tools)


    graph = StateGraph(State)
    graph.add_node("chat",chat_node)
    graph.add_node("tools",tool_node)
    graph.add_edge(START,"chat")
    graph.add_conditional_edges(
        "chat",
        tools_condition
    )
    graph.add_edge("tools","chat")

    return graph.compile()


# ==================================================
# MAIN
# ==================================================

async def main():

    chatbot = await build_graph()
    question = input("\nAsk something: ")
    result = await chatbot.ainvoke({"messages": [HumanMessage(content=question)]})

    print("\n==============================")
    print("FINAL ANSWER")
    print("==============================")

    print(result["messages"][-1].content)


if __name__ == "__main__":

    asyncio.run(main())