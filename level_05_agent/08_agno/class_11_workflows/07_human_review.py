"""
=====================================================================
 CLASS 11 | FILE 07: human_review.py
=====================================================================
 CONCEPT: HITL in Workflows — HumanReview
 Kya hai : Step(..., human_review=HumanReview(...)) se workflow kisi
           step pe ruk ke insaan se poochta hai:
             requires_confirmation=True  -> step chalane se PEHLE y/n
             requires_output_review=True -> step ke BAAD output dekho:
                                            approve / reject
           Pattern (agent HITL jaisa):
             run = workflow.run(...)
             while run.is_paused:
                 for req in run.active_step_requirements: req.confirm() / req.reject()
                 run = workflow.continue_run(run)
 Note    : HITL ke liye workflow ko db chahiye (paused run save hota hai).

   [Draft Post] ──▶ HUMAN: output theek? ──▶ [Publish] (HUMAN: confirm?)

 Run:
     uv run python class_11_workflows/07_human_review.py
=====================================================================
"""

from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.workflow import HumanReview, Step, StepInput, StepOutput, Workflow

from llm_setup import get_model

writer = Agent(name="Post Writer", model=get_model(),
               instructions=["Write a Facebook post, 40 words"])


def publish(step_input: StepInput) -> StepOutput:
    return StepOutput(content=f"PUBLISHED:\n{step_input.previous_step_content}")


workflow = Workflow(
    name="Publish Workflow",
    db=SqliteDb(db_file="tmp/class11.db"),
    steps=[
        Step(name="Draft Post", agent=writer,
             human_review=HumanReview(requires_output_review=True,
                                      output_review_message="Is this post okay?")),
        Step(name="Publish", executor=publish,
             human_review=HumanReview(requires_confirmation=True,
                                      confirmation_message="Publish this on Facebook?")),
    ],
)

run = workflow.run("Eid sale post for the Gold Dial Executive watch")

while run.is_paused:
    for req in run.active_step_requirements:
        print(f"\n[{req.step_name}]")
        if req.requires_output_review and req.step_output is not None:
            print("Output:", req.step_output.content)
            message = req.output_review_message
        else:
            message = req.confirmation_message
        answer = input(f"{message} (y/n): ").strip().lower()
        if answer == "y":
            req.confirm()
        else:
            req.reject()
    run = workflow.continue_run(run)

print("\n===== FINAL =====\n", run.content)
