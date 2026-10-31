"""
=====================================================================
 CLASS 09 | FILE 02: batch_and_async.py
=====================================================================
 CONCEPT: kickoff_for_each (batch) + async kickoff + async tasks
 Kya hai :
   1) crew.kickoff_for_each(inputs=[...]) -> same crew, bohot saare
      inputs (e.g. 50 products ki taglines) — ek ke baad ek.
   2) await crew.akickoff(...) -> async version. Kayi crews EK SAATH
      chalao (asyncio.gather) — kaam jaldi khatam.
   3) Task(async_execution=True) -> crew ke andar tasks parallel.
      Baad wala task context=[...] se un sab ka intezar karta hai.

 RULE    : Ek hi agent object ek waqt mein 2 kaam nahi kar sakta.
           Parallel kaam ke liye har job ka APNA agent/crew banao
           (isliye neeche make_crew() function hai).

 Run:
     uv run python class_09_yaml_project/02_batch_and_async.py
=====================================================================
"""

import asyncio

from crewai import Agent, Task, Crew

from llm_setup import get_llm

llm = get_llm()


def make_writer() -> Agent:
    return Agent(role="Product Copywriter", goal="Write 1-line product taglines",
                 backstory="You write short and memorable lines.", llm=llm)


def make_crew() -> Crew:
    writer = make_writer()
    task = Task(description="Write a 1-line tagline for the '{product}' watch.",
                expected_output="Only 1 line", agent=writer)
    return Crew(agents=[writer], tasks=[task])


# ================= 1) BATCH =================
products = [{"product": "Classic Steel"}, {"product": "Gold Executive"}, {"product": "Sports Silicone"}]
results = make_crew().kickoff_for_each(inputs=products)

print("\n===== BATCH RESULTS =====")
for p, r in zip(products, results):
    print(f"{p['product']:16} -> {r.raw}")


# ================= 2) ASYNC (kayi crews ek saath) =================
async def run_parallel():
    jobs = [make_crew().akickoff(inputs={"product": name})     # har job ki apni crew
            for name in ["Minimal White", "Black Chrono"]]
    return await asyncio.gather(*jobs)

print("\n===== ASYNC RESULTS =====")
for r in asyncio.run(run_parallel()):
    print("-", r.raw)


# ================= 3) ASYNC TASKS (crew ke andar parallel) =================
fb_writer, insta_writer, editor = make_writer(), make_writer(), make_writer()

fb_task = Task(description="Write a Facebook post for the Classic Steel watch (30 words).",
               expected_output="30 words", agent=fb_writer, async_execution=True)
insta_task = Task(description="Write an Instagram caption for the Classic Steel watch (15 words).",
                  expected_output="15 words", agent=insta_writer, async_execution=True)
combine = Task(description="Combine both posts into one list, with headings.",
               expected_output="Facebook: ... / Instagram: ...", agent=editor,
               context=[fb_task, insta_task])     # dono async tasks ka intezar

social_crew = Crew(agents=[fb_writer, insta_writer, editor], tasks=[fb_task, insta_task, combine])
print("\n===== ASYNC TASKS =====\n", social_crew.kickoff().raw)
