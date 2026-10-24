from agno.agent import Agent 
from agno.models.google import Gemini
from agno.models.ollama import Ollama
from agno.models.openrouter import OpenRouter
from agno.models.groq import Groq
from dotenv import load_dotenv
load_dotenv()
# ----------------------------------- using gemini -------------------------------------

# define the llm
llm = Gemini(id='gemini-2.5-flash')

# build agent
agent = Agent(
    name='first_agent',
    model=llm,
    markdown=True,
    stream=True
)

agent.print_response(input='Hi how are you?')


# ----------------------------------- using Ollama -------------------------------------

llm = Ollama(id='gpt-oss:20b-cloud', host='http://localhost:11434')

agent = Agent(
    name='first_agent',
    model=llm,
    markdown=True,
    stream=True
)

agent.print_response(input='Hi how are you?')


# ----------------------------------- using OpenRouter -------------------------------------

llm = OpenRouter(id='gpt-4o-mini')

agent = Agent(
    name='first_agent',
    model=llm,
    markdown=True,
    stream=True
)

agent.print_response(input='Hi how are you?')


# ----------------------------------- using Groq -------------------------------------

llm = Groq(id='openai/gpt-oss-120b')

agent = Agent(
    name='first_agent',
    model=llm,
    markdown=True,
    stream=True
)

agent.print_response(input='Hi how are you?')


agent.print_response(input='tell me what i asked you to do in the previous code snippet?')


# problem : 
# this file advantage and disadvantage is that it can use different llm models and print the response to the input but here is one problem when i ask what i asked you to do in the previous code snippet it will not be able to answer that question because it does not have memory so it will not be able to remember what i asked it to do in the previous code snippet.: 

# solve 
# so now i will show you how to add memory to the agent so that it can remember what i asked it to do in the previous code snippet and it will be able to answer that question.

# so go to next class .....
