"""
=====================================================================
 CLASS 02 | FILE 03: tool_decorator_toolkit.py
=====================================================================
 CONCEPT: @tool decorator options + Toolkit class + tool_call_limit
 Kya hai :
   @tool(...) se tool ka behaviour control karo:
     name / description   -> naam aur description override
     show_result=True     -> tool ka result seedha user ko dikhao
     stop_after_tool_call -> tool chalne ke baad agent ruk jaye
                             (model dobara na soche — result hi jawab)
     cache_results=True   -> same input pe dobara na chalao (cache)

   Toolkit class -> related tools ko ek "package" mein jama karo
                    (jaise DuckDuckGoTools). Settings/state class mein.

   Agent(tool_call_limit=3) -> ek run mein max 3 tool calls
                    (infinite loop aur zyada kharche se bachao)

 Run:
     uv run python class_02_tools/03_tool_decorator_toolkit.py
=====================================================================
"""

from agno.agent import Agent
from agno.tools import Toolkit, tool

from llm_setup import get_model


# ---------- 1) @tool decorator ----------
# TIP: Tool ka kam se kam 1 parameter rakho. Bina parameter wale tool pe
#      Groq ka gpt-oss model kabhi kabhi galat argument {"": {}} bhej deta hai.
@tool(name="get_store_timings", show_result=True, stop_after_tool_call=True)
def store_timings(day: str) -> str:
    """Returns the store opening and closing times.

    Args:
        day: Day the customer is asking about, e.g. 'Sunday'. Use 'today' if no day is mentioned.
    """
    if day.strip().lower() == "sunday":
        return "Sorry, the store is closed on Sunday. Mon-Sat: 11am - 10pm."
    return "Store timings: Mon-Sat 11am - 10pm, closed on Sunday."


@tool(cache_results=True, cache_ttl=3600)
def exchange_rate(currency: str) -> str:
    """Returns the PKR exchange rate (USD, AED, SAR). Cached for 1 hour."""
    rates = {"USD": 280, "AED": 76, "SAR": 75}
    rate = rates.get(currency.upper())
    return f"1 {currency.upper()} = {rate} PKR" if rate else "Currency not supported"


# ---------- 2) Toolkit class ----------
class OrderTools(Toolkit):
    def __init__(self, shop_name: str):
        self.shop_name = shop_name
        self.orders = {"1001": "Shipped", "1002": "Packing"}
        super().__init__(name="order_tools", tools=[self.order_status, self.cancel_order])

    def order_status(self, order_id: str) -> str:
        """Returns the status of an order."""
        return f"[{self.shop_name}] Order {order_id}: {self.orders.get(order_id, 'not found')}"

    def cancel_order(self, order_id: str) -> str:
        """Cancels an order (only if it has not shipped yet)."""
        if self.orders.get(order_id) == "Packing":
            self.orders[order_id] = "Cancelled"
            return f"Order {order_id} has been cancelled."
        return f"Order {order_id} cannot be cancelled."


agent = Agent(
    name="support_agent",
    model=get_model(),
    tools=[store_timings, exchange_rate, OrderTools(shop_name="TimeHouse")],
    tool_call_limit=3,          # ek run mein max 3 tool calls
    markdown=True,
)

agent.print_response("What is the status of order 1002? And how many PKR is 1 USD?")
agent.print_response("When does the store open?")   # stop_after_tool_call: result hi final jawab
