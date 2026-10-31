"""
=====================================================================
 CLASS 11 | FILE 04: condition.py
=====================================================================
 CONCEPT: Condition (if / else in workflow)
 Kya hai : Condition(evaluator=fn, steps=[...], else_steps=[...])
             evaluator(step_input) -> True  -> steps chalenge
                                   -> False -> else_steps chalenge
 Example : Email draft mein "Subject" line hai?
             Haan -> seedha final output
             Nahi -> Fixer agent subject line add karega

 Run:
     uv run python class_11_workflows/04_condition.py
=====================================================================
"""

from agno.agent import Agent
from agno.workflow import Condition, Step, StepInput, StepOutput, Workflow

from llm_setup import get_model

draft_agent = Agent(name="Email Drafter", model=get_model(),
                    instructions=["Write a professional email based on the user's request"])
fixer_agent = Agent(name="Subject Fixer", model=get_model(),
                    instructions=["Add a 'Subject: ...' line at the top of the email, keep the rest the same"])


def has_subject(step_input: StepInput) -> bool:
    email = (step_input.previous_step_content or "").lower()
    found = "subject" in email
    print(f"   [condition] subject line hai? {found}")
    return found


def final_output(step_input: StepInput) -> StepOutput:
    return StepOutput(content=step_input.previous_step_content)


workflow = Workflow(
    name="Email Workflow",
    steps=[
        Step(name="Draft Email", agent=draft_agent),
        Condition(
            name="Subject Check",
            evaluator=has_subject,
            steps=[Step(name="Use As Is", executor=final_output)],      # True
            else_steps=[Step(name="Add Subject", agent=fixer_agent)],   # False
        ),
    ],
)

workflow.print_response("Write an email to the team about a meeting tomorrow at 6 pm, do not write a subject", markdown=True)
