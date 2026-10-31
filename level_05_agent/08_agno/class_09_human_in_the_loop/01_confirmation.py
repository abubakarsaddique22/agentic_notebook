"""
=====================================================================
 CLASS 09 | FILE 01: confirmation.py
=====================================================================
 CONCEPT: HITL — Confirmation (tool chalne se pehle insaan ki "haan")
 Kya hai : HITL = Human-in-the-Loop. Khatarnak tools (refund, delete,
           email bhejna, payment) agent ki marzi pe nahi chalne chahiyein.
           @tool(requires_confirmation=True) lagao:
             1) agent.run() tool call pe RUK jata hai (is_paused = True)
             2) aap requirement dekh ke confirm() ya reject() karte ho
             3) agent.continue_run(...) -> kaam wahin se aage chalta hai

   run ──▶ tool chahiye ──▶ PAUSE ──▶ insaan: y / n ──▶ continue_run

 Run:
     uv run python class_09_human_in_the_loop/01_confirmation.py
=====================================================================
"""

from agno.agent import Agent
from agno.tools import tool

from llm_setup import get_model


@tool(requires_confirmation=True)
def cancel_order(order_id: str, reason: str) -> str:
    """Cancels a customer's order."""
    return f"Order {order_id} has been cancelled. Reason: {reason}"


agent = Agent(
    name="order_agent",
    model=get_model(),
    tools=[cancel_order],
    markdown=True,
)

run_output = agent.run("Cancel order 1002, the customer ordered the wrong size.")

# ---------- Agent ruk gaya? ----------
if run_output.is_paused:
    for requirement in run_output.active_requirements:
        if requirement.needs_confirmation:
            tool = requirement.tool_execution
            print(f"\nAgent ye tool chalana chahta hai: {tool.tool_name}({tool.tool_args})")
            answer = input("Allow karein? (y/n): ").strip().lower()
            if answer == "y":
                requirement.confirm()
            else:
                requirement.reject(note="The manager rejected this")

    run_output = agent.continue_run(run_response=run_output)

print("\n===== FINAL =====\n", run_output.content)
