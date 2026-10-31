"""
=====================================================================
 CLASS 11 | FILE 03: loop.py
=====================================================================
 CONCEPT: Loop (jab tak shart poori na ho, dobara karo)
 Kya hai : Loop(steps=[...], end_condition=fn, max_iterations=3)
             end_condition(outputs) -> True = ruk jao, False = dobara
             max_iterations         -> zyada se zyada kitni dafa
                                       (HAMESHA lagao — infinite loop se bachao)
 Kyun    : Quality loop — "jab tak story 100 words se kam na ho",
           "jab tak code ke tests pass na hon".

   ┌──────────────┐
   │ Story Writer │──▶ word count ok? ──No──┐
   └──────────────┘          │Yes            │
          ▲                  ▼               │
          └──────────────── done ◀───────────┘ (max 3 dafa)

 Run:
     uv run python class_11_workflows/03_loop.py
=====================================================================
"""

from agno.agent import Agent
from agno.workflow import Loop, Step, StepOutput, Workflow

from llm_setup import get_model

WORD_LIMIT = 120

story_agent = Agent(name="Story Writer", model=get_model(),
                    instructions=[f"Write a short story in LESS than {WORD_LIMIT} words"])


def short_enough(outputs: list[StepOutput]) -> bool:
    """True return karo to loop ruk jayega."""
    if not outputs:
        return False
    words = len(str(outputs[-1].content).split())
    print(f"   [loop check] {words} words")
    return words <= WORD_LIMIT


workflow = Workflow(
    name="Story Loop",
    steps=[
        Loop(
            name="Write Until Short",
            steps=[Step(name="Write Story", agent=story_agent)],
            end_condition=short_enough,
            max_iterations=3,
        )
    ],
)

workflow.print_response("A story about a magical watch in an old fort", stream=True, markdown=True)
