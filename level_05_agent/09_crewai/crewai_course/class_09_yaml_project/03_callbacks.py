"""
=====================================================================
 CLASS 09 | FILE 03: callbacks.py
=====================================================================
 CONCEPT: Callbacks (har step / har task ke baad apna code chalana)
 Kya hai :
   step_callback -> agent ke HAR step ke baad (khaas kar har tool call
                    ke baad) — agent kya kar raha hai live dekh lo
   task_callback -> HAR task khatam hone ke baad (Crew level)
   Task(callback=...) -> sirf us EK task ke baad
 Kyun    : Logging, progress bar, database mein save, Slack/WhatsApp
           pe notification — sab callbacks se hota hai.
 (Crew start/end ke liye @before_kickoff / @after_kickoff dekho:
  watch_review_crew/crew.py)

 Run:
     uv run python class_09_yaml_project/03_callbacks.py
=====================================================================
"""

from datetime import datetime

from crewai import Agent, Task, Crew, TaskOutput
from crewai.tools import tool

from llm_setup import get_llm


@tool("Get Today Sales")
def get_today_sales(day: str) -> str:
    """Returns today's order and return counts. Input: day, always pass 'today'."""
    return "orders=12, returns=2, top_product=Classic Steel"


def on_step(step):
    # step = agent ka ek qadam (tool ka result ya final jawab)
    print(f"   [STEP {datetime.now():%H:%M:%S}] {type(step).__name__}: {str(step)[:60]}")


def on_task_done(output: TaskOutput):
    print(f"\n   [TASK DONE] agent='{output.agent}' | {len(output.raw.split())} words")


def notify_manager(output: TaskOutput):
    # Asal mein yahan email / WhatsApp bhej sakte ho
    print(f"   [NOTIFY] Manager ko bheja: '{output.raw[:50]}...'")


agent = Agent(role="Store Reporter", goal="Write short daily reports",
              backstory="You always get data from the tool before writing a report.",
              tools=[get_today_sales], llm=get_llm())

t1 = Task(description="Get today's sales from the tool and write a one-line summary.",
          expected_output="1 line", agent=agent)
t2 = Task(description="Based on the summary, give 1 suggestion for tomorrow.",
          expected_output="1 line", agent=agent,
          callback=notify_manager)            # sirf is task ke baad

crew = Crew(
    agents=[agent],
    tasks=[t1, t2],
    step_callback=on_step,        # har step
    task_callback=on_task_done,   # har task
)

print("\n===== RESULT =====\n", crew.kickoff().raw)
