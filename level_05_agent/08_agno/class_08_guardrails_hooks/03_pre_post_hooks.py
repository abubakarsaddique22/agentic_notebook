"""
=====================================================================
 CLASS 08 | FILE 03: pre_post_hooks.py
=====================================================================
 CONCEPT: Pre-hooks aur Post-hooks (sirf security nahi — har kaam)
 Kya hai : Hook = aap ka function jo run se PEHLE ya BAAD chalta hai.
           Guardrail bhi asal mein ek pre-hook hi hai.
   pre_hooks  -> run se pehle. Parameter: run_input, agent, user_id ...
                 Use: logging, input saaf karna, rate limit, auth check
   post_hooks -> run ke baad. Parameter: run_output, agent ...
                 Use: logging, output badalna (signature lagana),
                      database mein save, analytics
 Note    : Hook ke parameters NAAM se milte hain — jo chahiye wahi likho.

 Run:
     uv run python class_08_guardrails_hooks/03_pre_post_hooks.py
=====================================================================
"""

import re
from datetime import datetime

from agno.agent import Agent
from agno.run.agent import RunOutput

from llm_setup import get_model


# ---------- PRE hooks ----------
def log_request(run_input, user_id) -> None:
    print(f"[PRE  {datetime.now():%H:%M:%S}] user={user_id} | input='{run_input.input_content_string()[:50]}'")


def clean_input(run_input) -> None:
    # Extra spaces aur "!!!!!!" saaf karo
    text = run_input.input_content_string()
    text = re.sub(r"!+", "!", text)
    run_input.input_content = " ".join(text.split())


# ---------- POST hooks ----------
def add_signature(run_output: RunOutput) -> None:
    run_output.content = f"{run_output.content}\n\n— TimeHouse Support Team"


def log_usage(run_output: RunOutput) -> None:
    tokens = run_output.metrics.total_tokens if run_output.metrics else 0
    print(f"[POST] tokens used = {tokens}")


agent = Agent(
    name="hooked_agent",
    model=get_model(),
    pre_hooks=[log_request, clean_input],
    post_hooks=[add_signature, log_usage],
    markdown=True,
)

result = agent.run("How   many   days   does   delivery   take!!!!!!", user_id="ali_123")
print("\nFINAL:\n", result.content)
