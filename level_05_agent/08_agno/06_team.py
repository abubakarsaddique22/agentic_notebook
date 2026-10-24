import os
from agno.agent import Agent
from agno.team import Team
from agno.models.groq import Groq
from agno.tools.tavily import TavilyTools
from dotenv import load_dotenv

# load the api keys
load_dotenv()

# quick sanity check so a missing key fails loudly instead of hanging silently
# assert os.environ.get("GROQ_API_KEY"), "GROQ_API_KEY not found - check your .env"
# assert os.environ.get("TAVILY_API_KEY"), "TAVILY_API_KEY not found - check your .env"

# # 2 agents
# ## 1. News search agent
# ## 2. Web Search agent

# # define the model
# llm = Groq(id="openai/gpt-oss-120b")

# # news search agent
# news_agent = Agent(
#     name="News Agent",
#     model=llm,
#     role="Get the latest news headlines and give summary",
#     instructions=[
#         "You are a news search agent",
#         "Search for the latest news for a particular destination and give a summarized view",
#     ],
#     tools=[TavilyTools()],
# )

# # web search agent
# web_search_agent = Agent(
#     name="Web Search Agent",
#     model=llm,
#     role="Get information for places to visit at the destination",
#     instructions=[
#         "You are a web search agent",
#         "your goal is to search for places of interest for a particular destination",
#     ],
#     tools=[TavilyTools()],
# )

# # form the team
# travel_agent = Team(
#     members=[news_agent, web_search_agent],
#     model=llm,
#     name="Travel Agent",
#     mode="route",  # leader routes the query to whichever single agent fits best -> much faster than coordinate
#     role="You are a team leader and you delegate tasks to members",
#     instructions=[
#         "You are an expert travel agent",
#         "your team members can get latest news and places of interest for a particular destination",
#         "your task is to present the output using proper headlines",
#     ],
#     markdown=True,
#     debug_mode=True,  # set to False once things are working reliably
# )

# travel_agent.cli_app(stream=True, markdown=True)



# ----------------------------------------------todo list -----------------------------------------------

from agno.db.sqlite import SqliteDb

# create the db
db = SqliteDb(db_file="team_db/demo.db",
              session_table="session_table")

# define my model

llm = Groq(id="openai/gpt-oss-120b")

# build a team of agents that maintains 3 lists in session state
## session_state= {groceries_list:[], todo_list:[], study_list:[]}

def add_item(session_state: dict, list_name: str, item_name: str) -> str:
    """Add item to the specified list"""
    item_name = item_name.lower()
    list_name = list_name.lower()
    session_state[list_name].append(item_name)
    return f"The item {item_name} added to {list_name}"


def remove_item(session_state: dict, list_name: str, item_name: str) -> str:
    """Remove item from the specified list"""
    item_name = item_name.lower()
    list_name = list_name.lower()
    session_state[list_name].remove(item_name)
    return f"The item {item_name} removed from the {list_name}"


def list_items(session_state: dict, list_name: str) -> str:
    """List items in the specified list"""
    list_name = list_name.lower()
    text = "\n".join([f"- {item}" for item in session_state[list_name]])
    return f"The items in the {list_name} are {text}"


def clear_list(session_state: dict, list_name: str) -> str:
    """Clears the specified list of all items"""
    list_name = list_name.lower()
    session_state[list_name].clear()
    return f"list: {list_name} cleared of all items"


# define the grocery agent
grocery_agent = Agent(
    id="grocery_agent",
    name="Grocery Agent",
    role="Manages list of items in a Grocery List",
    instructions=["You are an expert in managing grocery lists",
                  "you can add or remove item from the list",
                  "you can also see the items in the list",
                  "you can clear the list of items if asked to do so"],
    model=llm,
    tools=[add_item, remove_item, list_items, clear_list]
)


# define the todo list agent
todo_agent = Agent(
    id="todo_agent",
    name="ToDo Agent",
    role="Manages list of items in a To Do List",
    instructions=["You are an expert in managing Todo lists",
                  "you can add or remove item from the list",
                  "you can also see the items in the list",
                  "you can clear the list of items if asked to do so"],
    model=llm,
    tools=[add_item, remove_item, list_items, clear_list]
)


# define the study list agent
study_agent = Agent(
    id="study_agent",
    name="Study Agent",
    role="Manages list of items in a Study List",
    instructions=["You are an expert in managing Study lists",
                  "you can add or remove item from the list",
                  "you can also see the items in the list",
                  "you can clear the list of items if asked to do so"],
    model=llm,
    tools=[add_item, remove_item, list_items, clear_list]
)


# define the team
list_manager = Team(
    name="Personal List Manager",
    db=db,
    members=[grocery_agent, todo_agent, study_agent],
    role="You ar an expert team leader that manages sub agents with great accuracy",
    instructions=["You are an expert in managing different types of personal lists",
                  "The lists are: groceries_list, study_list, todo_list",
                  "The groceries_list is {groceries_list}",
                  "The todo list is {todo_list}",
                  "The study list is {study_list}",
                  "Make sure to use the list names as mentioned",
                  "your task is to manage these three lists where you can add, remove, list down items or clear any specified list",
                  "decide the name of the list based on user query",
                  "tasks will be handled by the members, you just delegate what to do"],
    model=llm,
    stream=True,
    markdown=True,
    session_state={"groceries_list":[], "todo_list":[], "study_list":[]},
    add_session_state_to_context=True,
    add_history_to_context=True,
    num_history_runs=3
)


list_manager.cli_app(stream=True, markdown=True)