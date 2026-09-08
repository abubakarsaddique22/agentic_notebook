# Note: 
# Here we will learn agent ai with memory and I have two types of memory one is short term 
# memory and one is long term memory  and in short term memory have two types like session and session state/agent state 
# and long term memeory have only user memory 

# short term memory :
# if I  use chat with chatgpt so many coversation tab show of left side so each coversation
#  is session in agno  and if use any session so session use stm 

# long term memory :
# if I  chat with chatgpt so many coversation show left side so as a users we can many coversation start 
# so as a user in agno user memory and use long term memory




# -------------------------------------------------------
# STM
# ---------------------------------------------------------



from agno.agent import Agent
from agno.models.google import Gemini
from agno.models.ollama import Ollama
from agno.db.sqlite import SqliteDb
from dotenv import load_dotenv
load_dotenv()

# --------------------------------- for one session-----------------------------------------------------

# # define llm
# llm = Gemini(id='gemini-2.5-flash')

# # add session id
# session_id = 'session_01'

# # add database
# db = SqliteDb()

# # define agent
# agent = Agent(
#     name='agent_with_memory',
#     model=llm,
#     # add memory parameter
#     db=db,
#     session_id=session_id,
#     add_history_to_context=True, # provide context to the model from previous conversation
#     num_history_runs=5, # number of previous conversation to provide context to the model

#     markdown=True,
#     stream=True
# )

# agent.print_response('my name is abubakar saddique and I am Ai Engineer')
# agent.print_response(input="tell me a joke that is funny")

# agent.print_response('can you tell me who am i?')


# # show all history 
# messages = agent.get_chat_history(session_id)
# for message in messages:
#     role, content = message.role, message.content
#     if role == "system":
#         continue
#     else:
#         print(f"Role: {role}, Message: {content}")


# --------------------------------- for many session-----------------------------------------------------

# llm = Ollama(id='gpt-oss:20b-cloud', host='http://localhost:11434')

# # create sessions
# session_transformer = "session_transformer"
# session_rag = "session_rag"

# # create a database
# db = SqliteDb(db_file="demo_01.db")


# agent = Agent(
#     model=llm,
#     db=db,
#     name="agent_with_memory",
#     add_history_to_context=True,
#     num_history_runs=5,
#     stream=True,
#     markdown=True
# )



# # # conversation 1 --> session_id=session_transformer
# agent.print_response("hi, can you tell me about transformer architecture in 100 words, make it simple", session_id=session_transformer)

# agent.print_response("what is self attention. explain in a single paragraph.", session_id=session_transformer)

# agent.print_response("what is this conversation all about?", session_id=session_transformer)


# # # conversation 2 --> session_id=session_rag
# agent.print_response("what is the role of RAG in AI. explain in 100 words",session_id=session_rag)

# agent.print_response("What does RAG stands for?",session_id=session_rag)

# agent.print_response("What is this conversation all about?",session_id=session_rag)


# # if i want start any conversation then just add that session id like i want about more question or discusse with rag session 
# agent.print_response(input="can you list down the advantages of RAG you talked about earlier. Only list down from previous chat", session_id=session_rag)

# print()
# print()


# # # show all history for every sessions 

# print("============ Tranformer Messages =================")
# messages_1 = agent.get_chat_history(session_transformer)

# for message in messages_1:
#     role, content = message.role, message.content
#     if role == "system":
#         continue
#     else:
#         print(f"Role: {role}, Message: \n{content}")
        
# print("\n\n============ RAG Messages =================")
# messages_2 = agent.get_chat_history(session_rag)

# for message in messages_2:
#     role, content = message.role, message.content
#     if role == "system":
#         continue
#     else:
#         print(f"Role: {role}, Message: \n{content}")




# -------------------------------------------- agent state/session state ------------------------

# Exmaple 1 : simple agent


session_id = 'first'
user_id = 'user_a'

# create session state 
user_info = {
    'name':'abubakar',
    'age' : 22
}

# define llm 
llm = Gemini(id='gemini-2.5-flash')

# build db 
db = SqliteDb(db_file='demo_02')


agent = Agent(
    model=llm,
    name='agent_with_session_state',
    user_id=user_id,
    session_id=session_id,
    session_state=user_info,
    add_session_state_to_context=True,
    db=db,
    markdown=True,
    stream=True
)

agent.print_response(input="Can you tell me my name and age")

# update session state 
agent.print_response(input="Can you tell me my name and age",
                     session_state={"name": "Neha", "age": 30})

agent.print_response(input="Can you tell me my name and age")

print(agent.get_session_state(session_id))



# okey now next check how to use tool with agent in state session 