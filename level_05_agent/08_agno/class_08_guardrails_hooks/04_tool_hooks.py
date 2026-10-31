"""
=====================================================================
 CLASS 08 | FILE 04: tool_hooks.py
=====================================================================
 CONCEPT: Tool Hooks (har tool call ke "beech" mein apna code)
 Kya hai : Tool hook ek "middleware" hai — tool chalne se pehle aur
           baad dono jagah control:
               def my_hook(function_name, function_call, arguments):
                   # PEHLE: check / log / block
                   result = function_call(**arguments)   # asal tool
                   # BAAD: result badlo / log karo
                   return result
           function_call na chalao = tool BLOCK (tool guardrail).
   Agent(tool_hooks=[...]) -> saare tools pe
   @tool(tool_hooks=[...]) -> sirf ek tool pe

 Example: refund 5000 se zyada ho to block, har tool ka time log.

 Run:
     uv run python class_08_guardrails_hooks/04_tool_hooks.py
=====================================================================
"""

import time

from agno.agent import Agent

from llm_setup import get_model


def issue_refund(order_id: str, amount: int) -> str:
    """Issues a refund to the customer. Inputs: order_id and amount (PKR)."""
    return f"Refund {amount} PKR order {order_id} has been processed."


def order_status(order_id: str) -> str:
    """Returns the status of an order."""
    return f"Order {order_id}: Shipped"


# ---------- Hook 1: timing log (sab tools) ----------
def timing_hook(function_name, function_call, arguments):
    start = time.time()
    result = function_call(**arguments)
    print(f"   [HOOK] {function_name}({arguments}) -> {time.time() - start:.3f}s")
    return result


# ---------- Hook 2: refund guardrail ----------
def refund_limit_hook(function_name, function_call, arguments):
    if function_name == "issue_refund" and int(arguments.get("amount", 0)) > 5000:
        print("   [HOOK] BLOCKED: 5000 se zyada refund manager approval ke baghair nahi")
        return "Refund blocked: refunds above 5000 PKR need manager approval."
    return function_call(**arguments)


agent = Agent(
    name="refund_agent",
    model=get_model(),
    tools=[issue_refund, order_status],
    tool_hooks=[timing_hook, refund_limit_hook],   # order mein chalte hain
    markdown=True,
)

agent.print_response("Tell me the status of order 1001.")
agent.print_response("Refund 9000 PKR for order 1002, use issue_refund.")
