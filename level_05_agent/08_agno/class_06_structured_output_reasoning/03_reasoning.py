"""
=====================================================================
 CLASS 06 | FILE 03: reasoning.py
=====================================================================
 CONCEPT: Reasoning (jawab se pehle "sochna")
 Kya hai : Mushkil sawalon (math, planning, comparison) pe agent ko
           step-by-step sochne do. Agno mein 2 tareeqe:
   1) ReasoningTools() -> agent ko "think" aur "analyze" tools milte
      hain. Wo kaam ke beech ruk ke sochta hai, phir result check
      karta hai. KISI BHI model ke saath chalta hai.
   2) reasoning_model=... -> ek alag NATIVE reasoning model pehle
      sochta hai, phir main model jawab likhta hai.
      Native = jo khud "thinking" karta hai: Groq gpt-oss-120b,
      DeepSeek-R1, OpenAI o3, Gemini thinking. Doosra model doge to
      Agno warning de ke normal tareeqe se chal jayega.
   show_full_reasoning=True -> soch ke steps terminal mein dikhao.

 Run:
     uv run python class_06_structured_output_reasoning/03_reasoning.py
=====================================================================
"""

from agno.agent import Agent
from agno.tools.reasoning import ReasoningTools

from llm_setup import get_model

question = (
    "I have 50,000 PKR. For my watch store I need to buy 6 watches at 4500 each "
    "and some watches at 3200 each, and keep 5000 for marketing. "
    "How many 3200 watches can I buy? Explain step by step."
)

# ---------- 1) ReasoningTools ----------
thinker = Agent(
    name="reasoning_agent",
    model=get_model(),
    tools=[ReasoningTools(add_instructions=True)],
    markdown=True,
)
thinker.print_response(question, show_full_reasoning=True, stream=True)

# ---------- 2) Alag reasoning model ----------
# Default .env (Groq gpt-oss-120b) khud native reasoning model hai
planner = Agent(
    name="planner_agent",
    model=get_model(),
    reasoning_model=get_model(),
    markdown=True,
)
planner.print_response("What are the 3 biggest risks of launching a new watch brand?")
