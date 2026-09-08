from crewai.flow.flow import Flow, start, listen, and_
from crewai import Agent
from crewai_tools import FileWriterTool
from dotenv import load_dotenv
from pydantic import BaseModel

# load up the api keys
load_dotenv()

# file writer tool
writer_tool = FileWriterTool()

# define a structured state
class AgentState(BaseModel):
    
    topic: str = ""
    notes: str = ""
    qa: str = ""


# create agentic flow
class MyConditionalAgent(Flow[AgentState]):
    
    # define the start node
    @start()
    def get_topic(self) -> str:
        topic = self.state.topic
        return topic
    
    @listen(get_topic)
    def create_notes(self, topic) -> str:
        # define the notes gen agent
        notes_agent = Agent(
            role=f"Expert Notes creator in topic: {topic}",
            goal=f"Generate 1000 words notes for the topic: {topic} and keep the notes organized and structured",
            backstory=f"You are an expert in the field of {topic}. You have an in depth understanding of the {topic} and can summarize key points using simple language"
        )
        
        notes_prompt = f"Create 1000 words notes for the {topic}. Your notes should be structured and in a markdown format. Keep the language simple and engaging."
        notes_response = notes_agent.kickoff(notes_prompt).raw
        
        # add notes to state
        self.state.notes = notes_response
        return notes_response
    
    @listen(get_topic)
    def create_qa(self, topic) -> str:
        # define the qa agent
        qa_agent = Agent(
            role=f"Expert MCQ Creator for topic: {topic}",
            goal=f"Generate 5 MCQ Question Answer pairs for the topic: {topic}. The QA pairs difficulty level should range from simple to advanced.",
            backstory=f"You are working as an examination paper incharge for the past 10 years. You have designed a lot of QA on various topics. Your examination has mixed questions ranging from easy to advanced levels"
        )
        
        qa_prompt = f"Create 5 MCQ based QA pairs for the topic: {topic}. The difficulty level of the questions should be mixed. Include easy, medium and advanced level questions. Output in markdown format"
        qa_response = qa_agent.kickoff(qa_prompt).raw
        
        # add qa to state
        self.state.qa = qa_response
        return qa_response
    
    # merge node --> merge notes and qa into one and write it to directory
    @listen(and_(create_notes, create_qa))
    def merge_notes_qa(self):
        notes = self.state.notes
        qa = self.state.qa
        
        # define the compiler agent
        compiler_agent = Agent(
            role="Expert in compiling information in markdown from various text sources",
            goal=f"Compile the information into a structured markdown from different sources and save it to a markdown file\n notes: {notes}\n qa:{qa}",
            backstory="You are an expert in compiling information into proper format inside markdown files. You do not change the information, just merge and compile them",
            tools=[writer_tool]
        )
        
        compiler_prompt=f"Based on the notes: {notes} and qa:{qa}, compile both of them into a mardown file where first are the notes followed by QA pairs. Do not change the data, just merge them into one file. Write down the compiled file as report.md"
        
        # write the md file using agent
        response = compiler_agent.kickoff(compiler_prompt).raw
        return response
    
if __name__ == "__main__":
    # create the flow
    flow = MyConditionalAgent()
    
    # execute the flow
    result = flow.kickoff({
        "topic": "Transformer Model in LLM"
    })
    
    # plot the flow
    flow.plot("conditional_agent.html")
    
    # print the flow output
    print(f"Flow Output: \n{result}")