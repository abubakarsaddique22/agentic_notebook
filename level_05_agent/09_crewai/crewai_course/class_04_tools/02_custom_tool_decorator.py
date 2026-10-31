"""
=====================================================================
 CLASS 04 | FILE 02: custom_tool_decorator.py
=====================================================================
 CONCEPT: Custom Tool with @tool decorator  (sab se asaan tareeqa)
 Kya hai : Koi bhi Python function ke upar @tool("naam") laga do —
           wo tool ban jata hai.
 ZAROORI : Function ki docstring (teen quotes wala text) hi tool ki DESCRIPTION
           hai. Agent isi ko parh ke decide karta hai ke tool kab use
           karna hai. Isliye docstring saaf likho!
           Type hints (str, int) se agent ko pata chalta hai ke kya
           input dena hai.

 Run:
     uv run python class_04_tools/02_custom_tool_decorator.py
=====================================================================
"""

from crewai import Agent, Task, Crew
from crewai.tools import tool

from llm_setup import get_llm

# Fake database (asal project mein ye Shopify / DB se aata)
STOCK = {"classic steel": 12, "black chrono": 0, "gold executive": 5}
PRICES = {"classic steel": 4500, "black chrono": 6800, "gold executive": 9999}


@tool("Check Stock")
def check_stock(product_name: str) -> str:
    """Checks the stock of a watch. Input: the product name, e.g. 'classic steel'."""
    qty = STOCK.get(product_name.lower().strip())
    if qty is None:
        return f"'{product_name}' product not found. Available: {list(STOCK)}"
    return f"{product_name}: {qty} pieces in stock"


@tool("Calculate Total")
def calculate_total(product_name: str, quantity: int) -> str:
    """Calculates the total price of a product in PKR. Inputs: product name and quantity."""
    price = PRICES.get(product_name.lower().strip())
    if price is None:
        return "Product not found."
    total = price * quantity
    delivery = 0 if total > 3000 else 250
    return f"Total: {total} PKR + delivery {delivery} PKR = {total + delivery} PKR"


# Tool ko direct test bhi kar sakte ho (bina agent ke):
print("Direct test:", check_stock.run(product_name="classic steel"))

sales_agent = Agent(
    role="Sales Assistant",
    goal="Give customers correct stock and price answers",
    backstory="You always check with the tools before answering and never guess.",
    tools=[check_stock, calculate_total],
    llm=get_llm(),
    verbose=True,
)

task = Task(
    description="The customer is asking: 'Can I get 2 gold executive watches? What will the total be?'",
    expected_output="A polite reply with the stock status and total price.",
    agent=sales_agent,
)

print("\n===== ANSWER =====\n", Crew(agents=[sales_agent], tasks=[task]).kickoff().raw)
