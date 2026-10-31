"""
=====================================================================
 CLASS 08 | FILE 02: custom_guardrail.py
=====================================================================
 CONCEPT: Custom Guardrails (input + output)
 Kya hai :
   INPUT guardrail  -> BaseGuardrail class banao, check() mein rule
                       likho. Galat ho to InputCheckError raise karo.
                       Agent(pre_hooks=[MyGuardrail()])
   OUTPUT guardrail -> function jo run_output parhe. Galat jawab ho to
                       OutputCheckError raise karo.
                       Agent(post_hooks=[my_output_check])

 Example:
   Input  : sirf watch store se related sawal allow (topic guardrail)
   Output : jawab mein competitor brand ka naam ya "100% guarantee"
            jaisa jhoota daawa na ho

 Run:
     uv run python class_08_guardrails_hooks/02_custom_guardrail.py
=====================================================================
"""

from agno.agent import Agent
from agno.exceptions import CheckTrigger, InputCheckError, OutputCheckError
from agno.guardrails.base import BaseGuardrail
from agno.run.agent import RunOutput

from llm_setup import get_model


# ---------- INPUT guardrail ----------
class StoreTopicGuardrail(BaseGuardrail):
    """Sirf store related sawal allow karta hai."""

    allowed_words = ["watch", "ghari", "order", "delivery", "return", "price", "strap", "warranty"]

    def check(self, run_input) -> None:
        text = run_input.input_content_string().lower()
        if not any(word in text for word in self.allowed_words):
            raise InputCheckError(
                "Sorry, I can only help with watches and orders.",
                check_trigger=CheckTrigger.INPUT_NOT_ALLOWED,
            )

    async def async_check(self, run_input) -> None:
        self.check(run_input)


# ---------- OUTPUT guardrail ----------
BANNED_CLAIMS = ["100% guarantee", "lifetime warranty", "rolex original"]


def no_false_claims(run_output: RunOutput) -> None:
    text = str(run_output.content).lower()
    for claim in BANNED_CLAIMS:
        if claim in text:
            raise OutputCheckError(f"The reply contained a false claim: '{claim}'",
                                   check_trigger=CheckTrigger.OUTPUT_NOT_ALLOWED)


agent = Agent(
    name="store_bot",
    model=get_model(),
    pre_hooks=[StoreTopicGuardrail()],
    post_hooks=[no_false_claims],
    instructions=["You are the assistant of the TimeHouse watch store"],
)

for question in ["What is the price of the Classic Steel watch?", "Give me a biryani recipe"]:
    result = agent.run(question)
    print(f"\nQ: {question}\nStatus: {result.status}\nA: {result.content}")
