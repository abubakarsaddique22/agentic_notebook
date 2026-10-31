"""
=====================================================================
 CLASS 05 | FILE 01: llm_config.py
=====================================================================
 CONCEPT: LLM class (model connection + settings)
 Kya hai : crewai.LLM ek object hai jo kisi bhi model se baat karta hai.
           Model string ka format:  "provider/model-name"
             "ollama/gpt-oss:20b-cloud"   (is course ka default)
             "openai/gpt-oss-120b"        (Groq, base_url ke saath)
             "gpt-4o-mini"                (OpenAI default)
 Settings:
   temperature -> 0 = har dafa same, seedha jawab | 1 = creative
   max_tokens  -> jawab ki max lambai
   timeout     -> kitne second wait karna hai

 Is file mein:
   1) LLM ko DIRECT call karna (bina agent ke) — testing ke liye kaam ka
   2) Alag agents ko alag LLM dena (sasta model simple kaam ke liye)

 Run:
     uv run python class_05_llm_output_guardrails/01_llm_config.py
=====================================================================
"""

from crewai import Agent

from llm_setup import get_llm

# ---------- 1) Direct LLM call ----------
creative_llm = get_llm(temperature=0.9)   # creative
strict_llm = get_llm(temperature=0.0)     # factual

print("CREATIVE:", creative_llm.call("Suggest 3 names for a watch brand, names only."))
print("STRICT  :", strict_llm.call("What is 2 + 2? Only write the number."))

# Messages format (chat history jaisa) bhi de sakte ho:
messages = [
    {"role": "system", "content": "You answer everything in 1 line."},
    {"role": "user", "content": "What is CrewAI?"},
]
print("MESSAGES:", strict_llm.call(messages))

# ---------- 2) Har agent ka apna LLM ----------
poet = Agent(
    role="Poet", 
    goal="Write short poems",
    backstory="You love poetry.", 
    llm=creative_llm
    )

print("\nPOET:", poet.kickoff("Write a 2-line poem about time.").raw)

# ------------------------------------------------------------------
# Tip: Doosra provider try karna ho to .env mein LLM_PROVIDER badlo.
# Ya direct:  from crewai import LLM
#             llm = LLM(model="ollama/gpt-oss:20b-cloud", temperature=0.2)
# ------------------------------------------------------------------
