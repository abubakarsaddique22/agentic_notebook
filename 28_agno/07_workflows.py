from agno.agent import Agent
from agno.models.ollama import Ollama
from agno.workflow import Step, Workflow
from dotenv import load_dotenv

# load the api keys
# load_dotenv()

# create the model

llm = Ollama(
    id='deepseek-v3.1:671b-cloud',
    host='http://localhost:11434' 
)

# ================= Agents =======================
# essay writing agent
essay_writing_agent = Agent(
    id="essay-writing-agent",
    name="Essay Writing Agent",
    instructions=["You are an expert in writing essays",
                  "Write well structured essays on a variety of topics",
                  "Limit your response to a maximum of 500 words"],
    model=llm,
)

# extraction agent to extract imp points from the essay
extraction_agent = Agent(
    id="extraction-agent",
    name="Extraction Agent",
    instructions=["You are an expert at extracting important points from the generated essay",
                  "Summarize the key points in a concise manner",
                  "Your output should be in a good format"],
    model=llm,
    markdown=True
)

# ================= Step =====================
essay_writing_step = Step(
    name="Essay Writing Step",
    agent=essay_writing_agent,
    description="Generates an essay based on the user's topic"
)

extraction_step = Step(
    name="Information Extraction Step",
    agent=extraction_agent,
    description="Extracts important points from the essay generated in the previous step"
)


# =================== Workflow =======================

workflow = Workflow(
    id="essay-workflow",
    name="Essay Writing and Point Extraction Workflow",
    steps=[essay_writing_step, extraction_step],
    description="A workflow that first writes an essay on a given topic and then extracts important points from that essay"
)

# execute the workflow
workflow.print_response(input="The topic is: Impact of technology on education. Respond in a proper format",
                        stream=True, markdown=True)




# ------------------------------- parallel workflow ---------------------------------

from agno.agent import Agent
from agno.models.ollama import Ollama
from agno.workflow import Step, Workflow, Parallel
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.hackernews import HackerNewsTools
from dotenv import load_dotenv

# load the api keys
load_dotenv()

# define the model
llm = Ollama(
    id='deepseek-v3.1:671b-cloud',
    host='http://localhost:11434' 
)

# ======================== Agents ==============================

# duckduckgo agent
duckduckgo_agent= Agent(
    id="duckduckgo-agent",
    name="DuckDuckGo Search Agent",
    instructions=["You are an expert web search agent using duckduckgo search",
                  "Provide accurate and relevant information based on user input",
                  "add heading to the output Source: DuckDuckGo Search"],
    model=llm,
    tools=[DuckDuckGoTools()],
)


# hackernews agent
hackernews_agent = Agent(
    id="hackernews-agent",
    name="HackerNews Agent",
    instructions=["You are an expert in retrieving trending topics and latest news from Hacker News",
                  "Add heading Source: HackerNews"],
    model=llm,
    tools=[HackerNewsTools()],
)


# report generation agent
report_generation_agent = Agent(
    id="report-generation-agent",
    name="Report Generation Agent",
    model=llm,
    instructions=["you are an expert in report generation",
                  "Compile all the information from various sources into a coherent and comprehensive report",
                  "use the information from both Google Search and DuckDuckGo search",
                  "mention the source of information in the report"
                  "The output should be in a proper format"],
    markdown=True
)


# ===================== Steps =============================

# duckduckgo search step
duckduckgo_search_step = Step(
    name="DuckDuckGo Search Step",
    agent=duckduckgo_agent,
    description="Performs a web search using DuckDuckgo Search"
)

# hackernews search step
hackernews_search_step = Step(
    name="Hackernews Search Step",
    agent=hackernews_agent,
    description="Performs the latest news search on HackerNews"
)

# report generation step
report_generation_step = Step(
    name="Report Generation Step",
    agent=report_generation_agent,
    description="Generates a report compiling information gathered from various sources"
)

# parallel steps
parallel_steps = Parallel(
    hackernews_search_step, duckduckgo_search_step,
    name="Parallel Search Step",
    description="Perform searches from various sources parallely"
)



# ======================== Workflow ===================================
parallel_workflow = Workflow(
    id="parallel-workflow",
    name="Retrieval and Report Generation Workflow",
    steps=[parallel_steps, report_generation_step],
    description="A workflow that performs web searching using multiple agents in parallel and then generates a report based on the retrieved information"
)


parallel_workflow.print_response(input="topic: AI",
                                 stream=True,
                                 markdown=True)



# ------------------------------------------ looping workflow ---------------------------------
from agno.agent import Agent
from agno.models.ollama import Ollama
from agno.workflow import Workflow, Step, Loop, StepOutput
# from dotenv import load_dotenv

# # load the api keys
# load_dotenv()

# create the model
model = Ollama(
    id='deepseek-v3.1:671b-cloud',
    host='http://localhost:11434' 
)

def word_count_condition(step_output: list[StepOutput]) -> bool:
    """Condition to check if the story is less than 300 words"""
    # check if there is output from the prev step
    if step_output:
        # looping through the list of step output
        for output in step_output:
            # fetching the content
            story_content: str = output.content
            # calculating the word count
            word_count: int = len(story_content.split(" "))
            # checking if word count is less than 300 words
            if word_count <= 300:
                return True
            else:
                return False
    else:
        return False


# ========================== Agent =======================

# story generation agent
story_generation_agent = Agent(
    id="story-generation-agent",
    name="Story Generation Agent",
    instructions=["You are an expert story writer.",
                  "Create engaging and imaginative short stories based on user request",
                  "stick to the word limit requested by user"],
    model=model
)


# =============================== Steps ============================

# create agent step
story_generation_step = Step(
    name="Story Generation Step",
    agent=story_generation_agent,
    description="Generates a short story based on user's prompt"
)

# define the looping step
looping_step = Loop(
    steps=[story_generation_step],
    name="Story generation loop",
    description="Generates stories in loop till condition is met",
    end_condition=word_count_condition
)

# ========================= Workflow ================================
workflow = Workflow(
    id="story-generation-workflow",
    name="Story Generation Workflow",
    steps=[looping_step],
    description="A worflow that generates short stories and ensures they are less than 300 words using a looping mechanism"
)


# input to the workflow
workflow.print_response(input="Title: A magical adventure in a castle and word count: 100 words",
                        stream=True,
                        markdown=True)


# -------------------------------------------- condtional workflow ---------------------------------

from agno.agent import Agent
from agno.models.ollama import Ollama
from agno.workflow import Step, Workflow, Condition, StepInput, StepOutput
# from dotenv import load_dotenv

# load the api keys
# load_dotenv()

# create the model
llm = Ollama(
    id='deepseek-v3.1:671b-cloud',
    host='http://localhost:11434' 
)

def review_email_condition(step_input: StepInput) -> bool:
    """Condition to check if the email has the subject line"""
    email_content = step_input.previous_step_content or ""
    if email_content:
        # content of the email
        email_content = email_content.lower()
        # check if subject is present
        if "subject" in email_content:
            return True
        else:
            return False
    else:
        return False


def email_output(step_input: StepInput) -> StepOutput:
    """Returns the output of the drafting step"""
    email_content = step_input.get_step_content("Email Draft Step")
    
    return StepOutput(content=email_content,
                      step_name="Email Output Step",
                      executor_type="function")
    
    
# ===================== Agents =============================
# email draft agent

email_draft_agent = Agent(
    id="email-draft-agent",
    name="Email Draft Agent",
    instructions=["You are an expert in drafting emails",
                  "Draft clear and professional emails based on the user's input"],
    model=llm
)

# ======================= Steps ===========================
# email drafting step
email_draft_step = Step(
    name="Email Draft Step",
    agent=email_draft_agent,
    description="Drafts and email based on user's input prompt"
)

# email output step
email_output_step = Step(
    name="Email output Step",
    executor=email_output,
    description="Outputs my email to the end user"
)

# conditional step
review_email_step = Condition(
    evaluator=review_email_condition,
    steps=[email_output_step],
    name="Review Email Step",
    description="Reviews the drafted email if it contains the subject line"
)

# =================== Workflow ============================
workflow = Workflow(
    id="email-workflow",
    name="Email Drafting and Review Workflow",
    steps=[email_draft_step,review_email_step],
    description="A workflow that drafts an email based on user and reviews it if the subject line is present or not"
)


# execute the workflow
workflow.print_response(input="Draft an email to schedule a meeting with my technical team at 6pm and do not give a subject")




# ------------------------------------------- branching workflow ---------------------------------
from agno.agent import Agent
from agno.models.ollama import Ollama
from agno.workflow import Step, Workflow, Router, StepInput
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.hackernews import HackerNewsTools
from dotenv import load_dotenv


def is_tech_topic(step_input: StepInput) -> list[Step]:
    """Condition to check whether the input topic is technical or not"""
    
    tech_keywords = ["technology",
                     "tech",
                     "software",
                     "ai",
                     "artificial intelligence",
                     "machine learning", 
                     "computers",
                     "programming",
                     "hardware",
                     "internet",
                     "gadgets",
                     "electronics"]
    
    user_input = step_input.input or ""
    if user_input:
        user_input = user_input.lower()
        # check if any tech word in the input
        if any(keyword in user_input for keyword in tech_keywords):
            return [hackernews_search_step]
        else:
            return [duckduckgo_search_step]
        

# load the api keys
load_dotenv()

# define the model
model = Ollama(
    id='deepseek-v3.1:671b-cloud',
    host='http://localhost:11434' 
)


# ================== Agents =======================================

# duckduckgo search agent
duckduckgo_search_agent = Agent(
    id="duckduckgo-agent",
    name="DuckDuckGo Search Agent",
    model=model,
    tools=[DuckDuckGoTools()],
    instructions=["You are an expert web search agent.",
                  "Provide accurate and relevant information based on user's queries"]
)

# hackernews agent
hackernews_agent = Agent(
    id="hackernews-agent",
    name="HackerNews Search Agent",
    model=model,
    tools=[HackerNewsTools()],
    instructions=["You are an expert agent",
                  "You retrieve relevant and latest news from hacker news platform"]
)


# content creation agent
content_creation_agent = Agent(
    id="content-creation-agent",
    name="Content Creation Agent",
    model=model,
    instructions=["You are an expert in content creation and writing articles",
                  "You take in research data and create engaging, well structured articles",
                  "Format the content with proper headings, bullet points and clear conclusions"]
)


# ======================= Steps =================================

duckduckgo_search_step = Step(
    name="DuckDuckGo Search Step",
    agent=duckduckgo_search_agent,
    description="Performs web search using DuckDuckGo Search"
)

hackernews_search_step = Step(
    name="HackerNews Search Step",
    agent=hackernews_agent,
    description="This step Retrieves latest news and trending topics from Hacker news"
)

content_creation_step = Step(
    name="Content Creation Step",
    agent=content_creation_agent,
    description="Creates engaging articles based on the data provided"
)

# create the router step
router_step = Router(
    name="Topic Router Step",
    description="Routes the workflow based on whether the topic is tech based or not",
    choices=[duckduckgo_search_step, hackernews_search_step],
    selector=is_tech_topic
)

# =========================== Workflow ==========================

# create the workflow
workflow = Workflow(
    id="research-and-create-workflow",
    name="Research and Publish Article Workflow",
    steps=[router_step, content_creation_step],
    description="A workflow that researches a topic from different sources based on if the topic is tech related or not and writes an engaging article based on the research"
)

workflow.print_response(input="Create an article about latest events due to climate change",
                        stream=True, markdown=True)
