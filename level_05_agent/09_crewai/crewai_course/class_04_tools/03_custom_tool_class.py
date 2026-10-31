"""
=====================================================================
 CLASS 04 | FILE 03: custom_tool_class.py
=====================================================================
 CONCEPT: Custom Tool with BaseTool class (+ caching + result_as_answer)
 Kya hai : Jab tool ko settings/state chahiye (API key, DB connection),
           ya input ka strict format chahiye, to class wala tareeqa use
           karo:
             name         -> tool ka naam
             description  -> agent ke liye explanation
             args_schema  -> Pydantic model: input ke fields + validation
             _run()       -> asal kaam yahan hota hai

 Extra concepts:
   cache_function   -> same input pe dobara tool na chalao (result cache)
   result_as_answer -> tool ka output hi FINAL jawab ban jaye (agent
                       usay badal na sake). Exact data chahiye ho tab.
   max_usage_count  -> tool zyada se zyada kitni dafa use ho

 Run:
     uv run python class_04_tools/03_custom_tool_class.py
=====================================================================
"""

from pydantic import BaseModel, Field

from crewai import Agent, Task, Crew
from crewai.tools import BaseTool

from llm_setup import get_llm


# 1) Input ka format (schema)
class ConvertInput(BaseModel):
    amount: float = Field(..., description="Amount of PKR to convert")
    currency: str = Field(..., description="Target currency: USD, AED or SAR")


# 2) Tool class
class CurrencyConverterTool(BaseTool):
    name: str = "PKR Currency Converter"
    description: str = "Converts a PKR amount to USD, AED or SAR."
    args_schema: type[BaseModel] = ConvertInput

    # Demo rates (asal mein API se aate)
    rates: dict = {"USD": 0.0036, "AED": 0.013, "SAR": 0.0135}

    def _run(self, amount: float, currency: str) -> str:
        rate = self.rates.get(currency.upper())
        if rate is None:
            return f"Currency '{currency}' is not supported. Use: {list(self.rates)}"
        print(f"   [tool chal raha hai] {amount} PKR -> {currency}")
        return f"{amount} PKR = {round(amount * rate, 2)} {currency.upper()}"


# 3) Caching rule: True return karo to result cache ho jayega
def cache_only_small_amounts(args: dict, result: str) -> bool:
    return args.get("amount", 0) < 1_000_000


converter = CurrencyConverterTool()
converter.cache_function = cache_only_small_amounts

# Direct test
print("Direct test:", converter.run(amount=10000, currency="USD"))

agent = Agent(
    role="Finance Helper",
    goal="Show prices in other currencies",
    backstory="You help overseas Pakistani customers.",
    tools=[converter],
    llm=get_llm(),
    verbose=True,
)

task = Task(
    description="Tell me the price of a 9999 PKR watch in both USD and AED.",
    expected_output="The price in both currencies, 2 lines.",
    agent=agent,
)

print("\n===== ANSWER =====\n", Crew(agents=[agent], tasks=[task]).kickoff().raw)

# ------------------------------------------------------------------
# result_as_answer example (sirf samajhne ke liye):
#   exact_tool = CurrencyConverterTool(result_as_answer=True)
#   Ab agent jo bhi soche, final answer EXACTLY tool ka output hoga.
# ------------------------------------------------------------------
