from typing_extensions import TypedDict
from typing import Annotated ,Literal
import re 
from langgraph.graph import StateGraph,START,END
from langchain_groq import ChatGroq
from langgraph.graph.message import add_messages
from langchain_tavily import TavilySearch
from langgraph.prebuilt import tools_condition, ToolNode
from langgraph.checkpoint.memory import MemorySaver
from dotenv import load_dotenv

load_dotenv()

model = ChatGroq(model="openai/gpt-oss-120b")

class BotState(TypedDict):
    messages: Annotated[list, add_messages]


memory = MemorySaver()

tavily_tool = TavilySearch(max_results=2)

def multiply(a: int, b: int) -> int:
    """Multiply a and b
    Args:
        a (int): first int
        b (int): second int
    Returns:
        int: output int
    """
    return a * b

tools = [tavily_tool,multiply]
tool_with_llm = model.bind_tools(tools)


def chatbot(state: BotState):
     return {"messages": tool_with_llm.invoke(state["messages"])}

bot_graph = StateGraph(BotState)
bot_graph.add_node('chatbot',chatbot)
bot_graph.add_node("tools",ToolNode(tools))

bot_graph.add_edge(START,'chatbot')
bot_graph.add_conditional_edges(
   'chatbot',
   tools_condition
)
bot_graph.add_edge('tools','chatbot')

bot_app = bot_graph.compile(checkpointer=memory)


config = {"configurable":{'thread_id':'1'}}
response=bot_app.invoke({"messages":"Hello my name is abubakar"},config=config)
for m in response['messages']:
    m.pretty_print()


print("=================================================")
# test e.g
response=bot_app.invoke({"messages":"Hey what is my name"},config=config)

print(response['messages'][-1].content)