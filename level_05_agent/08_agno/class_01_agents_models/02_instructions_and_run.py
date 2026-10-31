"""
=====================================================================
 CLASS 01 | FILE 02: instructions_and_run.py
=====================================================================
 CONCEPT: Agent ko "batana" ke kaisa behave kare + run() ka result
 Kya hai :
   description      -> agent kaun hai (system prompt ka pehla hissa)
   instructions     -> rules ki list (har line ek rule)
   expected_output  -> jawab ka format
   additional_context -> extra info jo har dafa prompt mein jaye
   add_datetime_to_context=True -> aaj ki date/time pata ho

   agent.print_response() -> sirf print karta hai
   agent.run()            -> RunOutput object deta hai jise CODE mein
                             use kar sakte ho (content, metrics, etc)

 Run:
     uv run python class_01_agents_models/02_instructions_and_run.py
=====================================================================
"""

from agno.agent import Agent

from llm_setup import get_model

agent = Agent(
    name="career_coach",
    model=get_model(),
    description="You are a friendly career coach who helps Pakistani students.",
    instructions=[
        "Always reply in simple English",
        "Keep answers short and practical",
        "If the question is not about careers, politely decline",
    ],
    expected_output="3 numbered steps",
    additional_context="The user is a fresh Computer Science graduate.",
    add_datetime_to_context=True,
    markdown=True,
)

# ---------- 1) print_response ----------
agent.print_response("I want to become an AI Engineer. Where should I start?")

# ---------- 2) run() -> result code mein use karo ----------
result = agent.run("What is the first step to start freelancing?")

print("\n===== RunOutput =====")
print("Content :", result.content)        # jawab ka text
print("Model   :", result.model)
if result.metrics:
    print("Tokens  :", result.metrics.total_tokens)
