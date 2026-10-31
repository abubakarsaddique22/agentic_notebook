"""
=====================================================================
 CLASS 11 | FILE 01: sequential.py
=====================================================================
 CONCEPT: Workflow — sequential Steps (agent + Python function)
 Kya hai : Team = agents khud decide karte hain (autonomous).
           Workflow = AAP order fix karte ho (deterministic pipeline).
             Step(agent=...)    -> is step pe agent chalega
             Step(executor=fn)  -> is step pe normal Python function
           Har step ka output agle step ka input banta hai.
   Function step ka format:
       def fn(step_input: StepInput) -> StepOutput:
           pichla = step_input.previous_step_content
           return StepOutput(content="...")

   [Essay Agent] ──▶ [word_count (Python)] ──▶ [Summary Agent]

 Run:
     uv run python class_11_workflows/01_sequential.py
=====================================================================
"""

from agno.agent import Agent
from agno.workflow import Step, StepInput, StepOutput, Workflow

from llm_setup import get_model

essay_agent = Agent(name="Essay Writer", model=get_model(),
                    instructions=["Write a 200-word essay on the topic"])

summary_agent = Agent(name="Summarizer", model=get_model(),
                      instructions=["Give the 3 key points of the essay as bullets"], markdown=True)


def word_count(step_input: StepInput) -> StepOutput:
    """Normal Python step — LLM nahi, sirf ginti."""
    essay = step_input.previous_step_content or ""
    words = len(essay.split())
    print(f"   [python step] essay mein {words} words hain")
    return StepOutput(content=f"{essay}\n\n(Word count: {words})")


workflow = Workflow(
    name="Essay Pipeline",
    steps=[
        Step(name="Write Essay", agent=essay_agent),
        Step(name="Count Words", executor=word_count),
        Step(name="Summarize", agent=summary_agent),
    ],
)

workflow.print_response("Topic: The impact of technology on education", stream=True, markdown=True)

# Kisi khaas step ka output nikalna (run() se):
result = workflow.run("Topic: Freelancing in Pakistan")
for step in result.step_results or []:
    print(f"\n--- {step.step_name} ---\n{str(step.content)[:120]}...")
