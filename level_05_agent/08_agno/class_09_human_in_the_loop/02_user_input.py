"""
=====================================================================
 CLASS 09 | FILE 02: user_input.py
=====================================================================
 CONCEPT: HITL — User Input (tool ke kuch fields INSAAN bhare)
 Kya hai : Kabhi agent ke paas zaroori info nahi hoti (customer ka
           address) ya hum chahte hain ke koi field sirf insaan de
           (e.g. discount %). Iske liye:
             @tool(requires_user_input=True, user_input_fields=["address"])
           Agent baqi fields khud bharta hai, "address" ke liye ruk
           jata hai aur aap se poochta hai.

 Run:
     uv run python class_09_human_in_the_loop/02_user_input.py
=====================================================================
"""

from agno.agent import Agent
from agno.tools import tool

from llm_setup import get_model


@tool(requires_user_input=True, user_input_fields=["address"])
def place_order(product: str, quantity: int, address: str) -> str:
    """Places an order. The address will be collected from the customer."""
    return f"Order placed: {quantity} x {product}, deliver to: {address}"


agent = Agent(name="order_taker", model=get_model(), tools=[place_order], markdown=True)

run_output = agent.run("I want to order 2 Classic Steel watches.")

if run_output.is_paused:
    for requirement in run_output.active_requirements:
        if requirement.needs_user_input:
            print(f"\nTool: {requirement.tool_execution.tool_name}")
            values = {}
            for field in requirement.user_input_schema:
                if field.value is None:                      # jo agent nahi bhar saka
                    values[field.name] = input(f"{field.name} ({field.description or ''}): ")
            requirement.provide_user_input(values)

    run_output = agent.continue_run(run_response=run_output)

print("\n===== FINAL =====\n", run_output.content)
