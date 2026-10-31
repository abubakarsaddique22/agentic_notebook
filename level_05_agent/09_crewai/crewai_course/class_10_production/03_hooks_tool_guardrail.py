"""
=====================================================================
 CLASS 10 | FILE 03: hooks_tool_guardrail.py
=====================================================================
 CONCEPT: Execution Hooks (tool guardrail + tool-level HITL)
 Kya hai : Hooks = har tool call ya LLM call se PEHLE/BAAD chalne wala
           aap ka function.
             @before_tool_call -> tool chalne se pehle
                 return False  -> tool BLOCK (nahi chalega)
                 return None   -> tool chalne do
             @after_tool_call  -> tool ke result ko dekho/badlo
             @before_llm_call / @after_llm_call -> LLM calls ke liye
 Kyun    : Agent khud faisla karta hai ke tool kab chalana hai. Lekin
           "refund do", "file delete karo" jaise khatarnak tools pe
           hamara control hona chahiye:
             1) Rule-based guardrail: 5000 se zyada refund BLOCK
             2) HITL: chhota refund bhi insaan se poochh ke

 Jab terminal approval maange to "yes" likh ke Enter dabao
 ("no" ya kuch aur = refund block).

 Run:
     uv run python class_10_production/03_hooks_tool_guardrail.py
=====================================================================
"""

from crewai import Agent, Task, Crew
from crewai.tools import tool
from crewai.hooks import before_tool_call, after_tool_call

from llm_setup import get_llm


@tool("Issue Refund")
def issue_refund(order_id: str, amount: int) -> str:
    """Issues a refund to the customer. Inputs: order_id and amount (PKR)."""
    return f"Refund of {amount} PKR issued for order {order_id}."


# ---------- Hook 1: guardrail + HITL (sirf refund tool pe) ----------
@before_tool_call(tools=["issue_refund"])
def approve_refund(context):
    amount = int(context.tool_input.get("amount", 0))
    print(f"\n[HOOK] Agent refund dena chahta hai: {context.tool_input}")

    if amount > 5000:                                   # rule-based guardrail
        print("[HOOK] BLOCKED: 5000 PKR se zyada refund allowed nahi.")
        return False

    answer = context.request_human_input(               # HITL
        prompt=f"{amount} PKR refund - approve? (yes/no): "
    )
    return None if answer.strip().lower() in ("yes", "y") else False


# ---------- Hook 2: har tool result ka log ----------
@after_tool_call
def log_tool_result(context):
    print(f"[HOOK] Tool '{context.tool_name}' result: {context.tool_result}")
    return None      # None = result jaisa hai waisa rehne do


agent = Agent(
    role="Refund Agent",
    goal="Process valid refunds",
    backstory="You follow company policy.",
    tools=[issue_refund],
    llm=get_llm(),
)

task = Task(
    description="The watch in order 1003 arrived broken. Refund 4500 PKR to the customer.",
    expected_output="Whether the refund was done or not — 1 line.",
    agent=agent,
)

print("\n===== RESULT =====\n", Crew(agents=[agent], tasks=[task]).kickoff().raw)
