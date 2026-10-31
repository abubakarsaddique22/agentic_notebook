"""
=====================================================================
 CLASS 01 | FILE 03: multiple_models.py
=====================================================================
 CONCEPT: Alag alag model providers + Fallback models
 Kya hai : Agno 40+ providers support karta hai. Har provider ki apni
           class hai, sab ka use same hai:
             from agno.models.groq import Groq          -> Groq(id="openai/gpt-oss-120b")
             from agno.models.openrouter import OpenRouter -> OpenRouter(id="openai/gpt-4o-mini")
             from agno.models.ollama import Ollama      -> Ollama(id="llama3.2")
             from agno.models.google import Gemini      -> Gemini(id="gemini-2.5-flash")
           NOTE: OpenRouter mein model ka naam "company/model" hota hai.

 Fallback models: agar pehla model fail ho (rate limit, server down),
           Agno khud doosra model try karta hai. Production mein bohot
           kaam ka hai.

 Run:
     uv run python class_01_agents_models/03_multiple_models.py
=====================================================================
"""

from agno.agent import Agent
from agno.models.ollama import Ollama

from llm_setup import get_model

# ---------- 1) Ek hi agent, model object badal ke ----------
main_model = get_model()          # .env wala (e.g. Groq)
print("Main model:", main_model.id)

agent = Agent(model=main_model, markdown=True)
agent.print_response("In one line: what is an LLM?")

# ---------- 2) Fallback ----------
# Agar main model fail ho jaye to local Ollama try hoga
safe_agent = Agent(
    model=get_model(),
    fallback_models=[Ollama(id="gpt-oss:20b-cloud")],
    markdown=True,
)
safe_agent.print_response("In one line: why is a fallback model important?")

# ------------------------------------------------------------------
# Practice: .env mein LLM_PROVIDER=ollama ya openrouter karke ye file
# dobara chalao — code badle baghair model badal jayega.
# ------------------------------------------------------------------
