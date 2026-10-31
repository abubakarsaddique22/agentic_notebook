"""
=====================================================================
 CLASS 03 | FILE 04: conditional_task.py
=====================================================================
 CONCEPT: ConditionalTask (Crew ke andar if/else)
 Kya hai : Normal crew mein HAR task chalta hai. ConditionalTask sirf
           tab chalta hai jab uski condition True ho — warna SKIP.
           condition = ek function jo PICHLE task ka output leta hai
           aur True/False return karta hai.

   classify_task ──▶ condition: complaint hai?
                         ├─ True  ─▶ apology_task chalega
                         └─ False ─▶ apology_task SKIP

 Rules:
   - ConditionalTask crew ka PEHLA task nahi ho sakta
     (usay check karne ke liye pichla output chahiye)
   - Flow ka @router bhi if/else hai, lekin wo Flow ke liye hai.
     ConditionalTask ek hi Crew ke andar kaam karta hai.

 Run:
     uv run python class_03_processes/04_conditional_task.py
=====================================================================
"""

from typing import Literal

from pydantic import BaseModel
from crewai import Agent, Crew, Task
from crewai.tasks.conditional_task import ConditionalTask
from crewai.tasks.task_output import TaskOutput


from llm_setup import get_llm


class Classification(BaseModel):
    category: Literal["complaint", "question"]


# ---------- Condition function ----------
def is_complaint(output: TaskOutput) -> bool:
    """True = agla task chalao, False = skip."""
    if output.pydantic:
        return output.pydantic.category == "complaint"
    return "complaint" in output.raw.lower()


support = Agent(
    role="Customer Support Agent",
    goal="Understand customer messages and reply politely",
    backstory="You work at the TimeHouse watch store and always stay calm and polite.",
    llm=get_llm(),
)

classify_task = Task(
    description="Classify this customer message as 'complaint' or 'question': '{message}'",
    expected_output="The category of the message.",
    output_pydantic=Classification,
    agent=support,
)

apology_task = ConditionalTask(
    condition=is_complaint,                 # <-- sirf complaint pe chalega
    description="The customer complained: '{message}'. Write a 2-line apology "
                "and promise a call back within 24 hours.",
    expected_output="A 2-line apology.",
    agent=support,
)

crew = Crew(agents=[support], tasks=[classify_task, apology_task])

for msg in ["The glass of my watch broke after 2 days!", "Do you deliver to Multan?"]:
    result = crew.kickoff(inputs={"message": msg})
    print(f"\nMESSAGE : {msg}")
    print(f"CATEGORY: {result.tasks_output[0].pydantic.category}")
    if len(result.tasks_output) > 1 and result.tasks_output[1].raw:
        print(f"APOLOGY : {result.tasks_output[1].raw}")
    else:
        print("APOLOGY : (skipped — complaint nahi thi)")