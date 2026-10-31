"""
=====================================================================
 CLASS 10 | FILE 02: event_listeners.py
=====================================================================
 CONCEPT: Event Listeners (Observability / monitoring)
 Kya hai : CrewAI har cheez pe "event" bhejta hai: crew start, task
           complete, tool use, LLM call, etc. Aap BaseEventListener
           bana ke in events ko "sun" sakte ho.
 Kyun    : Production mein dekhna parta hai:
             - kaunsa tool kitni dafa chala, kitna time laga
             - kitne tokens (paise) lage
             - kahan error aaya
           Ye data log file, dashboard, ya Langfuse/LangSmith jaise
           tools mein bhej sakte ho.

 Run:
     uv run python class_10_production/02_event_listeners.py
=====================================================================
"""

from crewai import Agent, Task, Crew
from crewai.tools import tool
from crewai.events import BaseEventListener
from crewai.events.types.crew_events import CrewKickoffStartedEvent, CrewKickoffCompletedEvent
from crewai.events.types.task_events import TaskCompletedEvent
from crewai.events.types.tool_usage_events import ToolUsageFinishedEvent
from crewai.events.types.llm_events import LLMCallCompletedEvent

from llm_setup import get_llm


class MonitorListener(BaseEventListener):
    """Sab important events ko sun ke print/log karta hai."""

    def __init__(self):
        self.llm_calls = 0
        super().__init__()

    def setup_listeners(self, crewai_event_bus):

        @crewai_event_bus.on(CrewKickoffStartedEvent)
        def on_start(source, event):
            print(f"\n[MONITOR] Crew '{event.crew_name}' start | inputs={event.inputs}")

        @crewai_event_bus.on(TaskCompletedEvent)
        def on_task(source, event):
            print(f"[MONITOR] Task complete by '{event.output.agent}'")

        @crewai_event_bus.on(ToolUsageFinishedEvent)
        def on_tool(source, event):
            seconds = (event.finished_at - event.started_at).total_seconds()
            print(f"[MONITOR] Tool '{event.tool_name}' {seconds:.2f}s | cache={event.from_cache}")

        @crewai_event_bus.on(LLMCallCompletedEvent)
        def on_llm(source, event):
            self.llm_calls += 1

        @crewai_event_bus.on(CrewKickoffCompletedEvent)
        def on_end(source, event):
            print(f"[MONITOR] Crew done | LLM calls={self.llm_calls} | tokens={event.total_tokens}")


monitor = MonitorListener()     # bas object banana kaafi hai — listener ON


@tool("Get Delivery Days")
def get_delivery_days(city: str) -> str:
    """Returns the delivery days for a city."""
    return "1-2 days" if city.lower().strip() == "lahore" else "3-5 working days"


agent = Agent(role="Delivery Helper", goal="Tell the delivery time",
              backstory="You check with the tool before answering.",
              tools=[get_delivery_days], llm=get_llm())

task = Task(description="How many days will delivery to Peshawar take?",
            expected_output="A 1-line answer", agent=agent)

print("\n===== ANSWER =====\n", Crew(agents=[agent], tasks=[task], name="delivery_crew").kickoff().raw)
