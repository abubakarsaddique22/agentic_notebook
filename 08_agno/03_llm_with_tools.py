from agno.agent import Agent
from agno.models.openrouter import OpenRouter
from agno.models.ollama import Ollama
from agno.db.sqlite import SqliteDb
from agno.run import RunContext
from dotenv import load_dotenv

# Load API keys
load_dotenv()

# # ---------------------------------------- added CADU operation --------------------
# db = SqliteDb(db_file="session_state_db/shopping_02.db")

# # Session and user IDs
# session_id = "2"
# user_id = "user_a"
# # define llm 
# llm = OpenRouter(id="gpt-4o-mini")

# # ---------------------------------------------------------
# # Add item
# # ---------------------------------------------------------

# def add_item(run_context: RunContext, item: str) -> str:
#     """Add an item to the shopping list."""

#     item = item.lower()

#     # Get shopping list from session state
#     shopping_list = run_context.session_state["shopping_list"]

#     if item in shopping_list:
#         return f"{item} already in shopping list"

#     shopping_list.append(item)

#     return f"{item} added to the shopping list"


# # ---------------------------------------------------------
# # Remove item
# # ---------------------------------------------------------

# def remove_item(run_context: RunContext, item: str) -> str:
#     """Remove an item from the shopping list."""

#     item = item.lower()

#     # Get shopping list from session state
#     shopping_list = run_context.session_state["shopping_list"]

#     if item not in shopping_list:
#         return f"{item} not in shopping list. Add the item first"

#     shopping_list.remove(item)

#     return f"{item} removed from shopping list"


# # ---------------------------------------------------------
# # List items
# # ---------------------------------------------------------

# def list_items(run_context: RunContext) -> str:
#     """List all items in the shopping list."""

#     shopping_list = run_context.session_state["shopping_list"]

#     if shopping_list:
#         list_of_items = "\n".join(
#             [f"- {item}" for item in shopping_list]
#         )

#         return f"The shopping list is:\n{list_of_items}"

#     return "The shopping list is empty"


# # ---------------------------------------------------------
# # Clear list
# # ---------------------------------------------------------

# def clear_list(run_context: RunContext) -> str:
#     """Clear all items from the shopping list."""

#     shopping_list = run_context.session_state["shopping_list"]

#     shopping_list.clear()

#     return "Cleared the shopping list of all items"


# # ---------------------------------------------------------
# # Create agent
# # ---------------------------------------------------------

# agent = Agent(
#     model=llm,
#     name="agent_with_state",
#     # Initial session state
#     session_state={"shopping_list": []},
#     session_id=session_id,
#     user_id=user_id,
#     instructions="""
#     Your job is to manage shopping lists.

#     You can:
#     - Add items to the shopping list
#     - Remove purchased items
#     - List items
#     - Clear the entire shopping list

#     Always use the appropriate tool to modify or read the shopping list.
#     Do not claim an item was added, removed, or cleared if the tool failed.
#     """,
#     tools=[add_item,remove_item,clear_list,list_items],
#     db=db,
#     stream=True,
#     markdown=True
# )


# # ---------------------------------------------------------
# # Test 1
# # ---------------------------------------------------------

# agent.print_response("Can you tell me what is on the shopping list?")
# print(f"The session state is: {agent.get_session_state(session_id)}")

# agent.print_response("Add milk to the shopping list")
# print(f"The session state is: {agent.get_session_state(session_id)}")


# agent.print_response("Add eggs and bread to my shopping list")
# print(f"The session state is: {agent.get_session_state(session_id)}")

# agent.print_response("I have bought milk and eggs")
# print(f"The session state is: {agent.get_session_state(session_id)}")



# # --------------------------------------------------------CADR and with diffrent sessions ---


# # load the api keys
# load_dotenv()

# # build a db
# db = SqliteDb(db_file="session_state_db/shopping_02.db")

# # give a session id and user id
# user_id = "user_a"

# # create a model
# llm = Ollama(
#     id='qwen3-vl:235b-cloud',  # Use one of your local IDs
#     host='http://localhost:11434' 
# )

# # define a tool that adds items to shopping list
# def add_item(session_state: dict, item: str) -> str:
#     """Add an item to the shopping list"""
#     # lowercase the item
#     item = item.lower()
#     # fetch the shopping list
#     shopping_list = session_state["shopping_list"]
    
#     # check if item in list or not
#     if item in shopping_list:
#         return f"{item} already in shopping list"
#     else:
#         shopping_list.append(item)
#         return f"{item} added to the shopping list"


# # define tool to remove item from shopping list
# def remove_item(session_state: dict, item: str) -> str:
#     """Removes an item from the shopping list for the items i have already purchased"""
#     # lowercase the item
#     item = item.lower()
#     # fetch the shopping list
#     shopping_list = session_state["shopping_list"]
    
#     # check item in list or not
#     if item not in shopping_list:
#         f"{item} not in shopping list. Add the item first"
#     else:
#        # remove the item from shopping list
#        shopping_list.remove(item)
#        return f"{item} removed from shopping list"
       

# # define tool to read items from the list
# def list_items(session_state: dict) -> str:
#     """List down all the items in shopping list"""
#     # check whether shopping list is empty or not
#     # fetch the shopping list
#     shopping_list = session_state["shopping_list"]
    
#     if shopping_list:
#         list_of_items = "\n".join([f"- {item}" for item in shopping_list]) ## - Apple - Banana
#         return f"The shopping list is: {list_of_items}"
#     else:
#         return "The shopping list is empty"
    

# # define tool to clear the list
# def clear_list(session_state: dict) -> str:
#     """Clears the shopping list of all items and gives you empty list"""
#     shopping_list = session_state["shopping_list"]
#     shopping_list.clear()
#     return "Cleared the shopping list of all items"
        
# # create the agent
# agent = Agent(
#     model=llm,
#     name="agent_with_state",
#     instructions="Your job is to manage shopping lists. you start off with an empty list and you can add item to the list, remove item from the list if i have already bought them, list items in the list or clear the list of all items",
#     tools=[add_item, remove_item, clear_list, list_items],
#     user_id=user_id,
#     add_session_state_to_context=True,
#     db=db,
#     stream=True,
#     markdown=True
# )

# # create sessions
# fruits_session = "fruits_list"
# dairy_session = "dairy_list"

# # add items to my fruits list
# agent.print_response("Add apple to fruits list", 
#                     session_id=fruits_session,
#                     session_state={"shopping_list": []})
# print(f"The session state is: {agent.get_session_state(fruits_session)}")

# # add items to my dairy list
# agent.print_response("Add milk to dairy list", 
#                     session_id=dairy_session,
#                     session_state={"shopping_list": []})
# print(f"The session state is: {agent.get_session_state(dairy_session)}")

# agent.print_response("what is on my list",
#                     session_id=fruits_session)

# agent.print_response("what is on my list",
#                     session_id=dairy_session)

# agent.print_response("what is on my list",
#                     session_id=dairy_session)

# agent.print_response("I have already bought apple, please add banana and oranges to the list",
#                     session_id=fruits_session)

# agent.print_response("Clear the list and add pineapple to it",
#                     session_id=fruits_session)
# print("Fruit list", agent.get_session_state(fruits_session))

# agent.print_response("Add curd and butter to the list, and remove milk from the list",
#                     session_id=dairy_session)
# print("Dairy list", agent.get_session_state(dairy_session)) 


# ----------------------------- agent with search tool -----------------------------

from agno.tools.duckduckgo import DuckDuckGoTools


# create the model
llm = OpenRouter(id="gpt-4o-mini")


# create the web search tool
web_search = DuckDuckGoTools()

# create the agent
agent = Agent(
    name="agent_with_web_search",
    tools=[web_search],
    instructions="You are an expert in searching web. you have access to web search tool to get the latest information",
    model=llm,
    stream=True,
    markdown=True
)

agent.print_response("Get me news regarding Tukary Israel conflict")