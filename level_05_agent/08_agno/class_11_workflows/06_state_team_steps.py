"""
=====================================================================
 CLASS 11 | FILE 06: state_team_steps.py
=====================================================================
 CONCEPT: Workflow session_state + Team as a step + Steps group + db
 Kya hai :
   Workflow(session_state={...}) -> saare steps ka shared data.
       Function step: def fn(step_input, run_context: RunContext)
                      run_context.session_state["key"] = ...
   Step(team=...)  -> poori Team ek step ban sakti hai
   Steps([...])    -> kayi steps ko ek NAAM wale group mein rakho
                      (organize + reuse, e.g. "Quality Checks")
   Workflow(db=...) -> har run save hota hai (history, resume)

   [Plan (Team)] ──▶ Steps("Quality Checks": word check, tone check) ──▶ [Save (py)]

 Run:
     uv run python class_11_workflows/06_state_team_steps.py
=====================================================================
"""

from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.run import RunContext
from agno.team import Team
from agno.workflow import Step, StepInput, StepOutput, Steps, Workflow

from llm_setup import get_model

# ---------- Team as a step ----------
marketing_team = Team(
    name="Marketing Team",
    model=get_model(),
    members=[
        Agent(name="Copywriter", role="Writes a catchy post", model=get_model()),
        Agent(name="Hashtag Expert", role="Suggests 5 relevant hashtags", model=get_model()),
    ],
    instructions=["Prepare an Instagram post + hashtags"],
)


# ---------- Function steps jo shared state use karte hain ----------
def word_check(step_input: StepInput, run_context: RunContext) -> StepOutput:
    words = len((step_input.previous_step_content or "").split())
    run_context.session_state["word_count"] = words
    return StepOutput(content=step_input.previous_step_content)


def tone_check(step_input: StepInput, run_context: RunContext) -> StepOutput:
    text = (step_input.previous_step_content or "").lower()
    run_context.session_state["has_emoji_or_hashtag"] = "#" in text
    return StepOutput(content=step_input.previous_step_content)


def save_post(step_input: StepInput, run_context: RunContext) -> StepOutput:
    run_context.session_state["posts_saved"] += 1
    return StepOutput(content=f"Saved! (total saved: {run_context.session_state['posts_saved']})\n\n"
                              f"{step_input.get_step_content('Create Post')}")


workflow = Workflow(
    name="Post Factory",
    db=SqliteDb(db_file="tmp/class11.db"),
    session_id="post_factory",
    session_state={"posts_saved": 0},
    steps=[
        Step(name="Create Post", team=marketing_team),
        Steps(name="Quality Checks", steps=[
            Step(name="Word Check", executor=word_check),
            Step(name="Tone Check", executor=tone_check),
        ]),
        Step(name="Save", executor=save_post),
    ],
)

workflow.print_response("Launch post for the new Minimal White Dial watch", markdown=True)
print("\nWORKFLOW STATE:", workflow.get_session_state(session_id="post_factory"))
