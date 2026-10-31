"""
=====================================================================
 CLASS 12 | FILE 02: async_agents.py
=====================================================================
 CONCEPT: Async (arun / aprint_response) — kayi kaam ek saath
 Kya hai : Har method ka async version hai: run -> arun,
           print_response -> aprint_response, continue_run -> acontinue_run.
           asyncio.gather(...) se kayi agents/sawal EK SAATH chalao.
 Kyun    : Web server (FastAPI) async hota hai. 10 customers ke sawal
           line mein lagane ki bajaye ek saath handle karo.
 Test    : Neeche dekho — 3 sawal sequential vs parallel ka time.

 Run:
     uv run python class_12_production/02_async_agents.py
=====================================================================
"""

import asyncio
import time

from agno.agent import Agent

from llm_setup import get_model

agent = Agent(name="fast_agent", model=get_model(), instructions=["Answer in 1 line"])

questions = [
    "What is an analog watch?",
    "What is a chronograph?",
    "What does water resistant 50m mean?",
]


async def sequential():
    for q in questions:
        await agent.arun(q)


async def parallel():
    results = await asyncio.gather(*[agent.arun(q) for q in questions])
    for q, r in zip(questions, results):
        print(f"Q: {q}\nA: {r.content}\n")


start = time.time()
asyncio.run(sequential())
print(f"Sequential: {time.time() - start:.1f}s")

start = time.time()
asyncio.run(parallel())
print(f"Parallel  : {time.time() - start:.1f}s")
