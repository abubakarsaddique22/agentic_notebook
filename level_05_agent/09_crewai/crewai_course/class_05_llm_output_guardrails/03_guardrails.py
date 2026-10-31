"""
=====================================================================
 CLASS 05 | FILE 03: guardrails.py
=====================================================================
 CONCEPT: Guardrails (Task output ki "checking" / quality gate)
 Kya hai : Guardrail ek check hai jo task ke output ko AGLE step pe
           jaane se PEHLE validate karta hai.
             Pass  -> output aage chala jata hai
             Fail  -> error message agent ko wapas jata hai aur agent
                      DOBARA koshish karta hai (guardrail_max_retries tak)

 2 qisam ke guardrails:
   1) Function guardrail -> Python function, rules aap likhte ho
        return (True, output)          # pass
        return (False, "kya galat hai") # fail + agent ko feedback
   2) LLM guardrail (string) -> sirf English/Urdu mein rule likho,
        LLM khud check karega. e.g. "Jawab mein koi gaali na ho"

   guardrails=[...] -> kayi guardrails ek saath, order mein chalte hain.

 Run:
     uv run python class_05_llm_output_guardrails/03_guardrails.py
=====================================================================
"""

from crewai import Agent, Task, Crew, TaskOutput

from llm_setup import get_llm


# ---------- Function guardrail #1: lambai check ----------
def max_60_words(output: TaskOutput):
    words = len(output.raw.split())
    if words > 60:
        return (False, f"The answer has {words} words. Make it less than 60 words.")
    return (True, output.raw)


# ---------- Function guardrail #2: zaroori cheez maujood ho ----------
def must_have_hashtag(output: TaskOutput):
    if "#" not in output.raw:
        return (False, "Add at least 1 hashtag at the end.")
    return (True, output.raw)


writer = Agent(
    role="Social Media Writer",
    goal="Write Instagram captions for a watch store",
    backstory="You write short and catchy captions.",
    llm=get_llm(),
)

caption_task = Task(
    description="Write an Instagram caption for the launch of the new 'Gold Dial Executive' watch.",
    expected_output="One caption, under 60 words, with hashtags.",
    agent=writer,
    guardrails=[
        max_60_words,                                        # function
        must_have_hashtag,                                   # function
        "The caption must not contain any false claim (like 'lifetime warranty' or '100% original Rolex').",  # LLM
    ],
    guardrail_max_retries=3,   # 3 dafa tak dobara try
)

result = Crew(agents=[writer], tasks=[caption_task], verbose=True).kickoff()
print("\n===== PASSED CAPTION =====\n", result.raw)

# ------------------------------------------------------------------
# Sirf ek guardrail ho to:   Task(..., guardrail=max_60_words)
# Retries khatam aur phir bhi fail -> error raise hota hai.
# ------------------------------------------------------------------
