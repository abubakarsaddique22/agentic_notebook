"""
=====================================================================
 CLASS 09 | FILE 03: external_execution.py
=====================================================================
 CONCEPT: HITL — External Execution (tool AAP khud chalao)
 Kya hai : @tool(external_execution=True) -> agent sirf batata hai ke
           "ye tool in arguments ke saath chalao". Asal kaam aap ke
           code mein (ya kisi doosre system / insaan ke haath) hota hai,
           phir result wapas dete ho:
             requirement.set_external_execution_result("...")
 Kyun    : Payment gateway, bank API, ya koi kaam jo agent ke server
           pe nahi chalna chahiye (security). Agent sirf "plan" deta hai.

 Run:
     uv run python class_09_human_in_the_loop/03_external_execution.py
=====================================================================
"""

from agno.agent import Agent
from agno.tools import tool

from llm_setup import get_model


@tool(external_execution=True)
def charge_payment(customer_id: str, amount_pkr: int) -> str:
    """Charges a payment from the customer's account."""
    # Ye body kabhi nahi chalegi — asal kaam bahar hota hai


def my_secure_payment_system(customer_id: str, amount_pkr: int) -> str:
    """Asal mein yahan JazzCash / bank API call hoti."""
    return f"SUCCESS: {amount_pkr} PKR charged from {customer_id}, txn=TX-88231"


agent = Agent(name="billing_agent", model=get_model(), tools=[charge_payment], markdown=True)

run_output = agent.run("Charge 4500 PKR from customer C-501.")

if run_output.is_paused:
    for requirement in run_output.active_requirements:
        if requirement.needs_external_execution:
            args = requirement.tool_execution.tool_args
            print(f"\nAgent ne kaha: charge_payment({args}) chalao")
            result = my_secure_payment_system(**args)        # hum khud chalate hain
            print("Payment system result:", result)
            requirement.set_external_execution_result(result)

    run_output = agent.continue_run(run_response=run_output)

print("\n===== FINAL =====\n", run_output.content)
