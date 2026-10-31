"""
=====================================================================
 CLASS 05 | FILE 02: structured_output.py
=====================================================================
 CONCEPT: Structured Output (Pydantic / JSON)
 Kya hai : Normally agent free text deta hai. Lekin code mein use karne
           ke liye hamein fix format chahiye (e.g. name, price, tags).
           Pydantic model bana ke task ko do:
             output_pydantic=MyModel -> result.pydantic (Python object)
             output_json=MyModel     -> result.json_dict (dictionary)
 Kyun    : Agent ka jawab ab database, API, ya website mein seedha
           use ho sakta hai — parsing ka jhanjhat khatam.

 Run:
     uv run python class_05_llm_output_guardrails/02_structured_output.py
=====================================================================
"""

from pydantic import BaseModel, Field

from crewai import Agent, Task, Crew

from llm_setup import get_llm


# 1) Output ka shape define karo
class ProductListing(BaseModel):
    title: str = Field(description="Catchy product title")
    price_pkr: int = Field(description="Price in PKR")
    features: list[str] = Field(description="3 short features")
    tags: list[str] = Field(description="5 SEO tags")


copywriter = Agent(
    role="E-commerce Copywriter",
    goal="Create SEO-friendly product listings",
    backstory="You write listings for online stores that sell.",
    llm=get_llm(temperature=0.2),
)

task = Task(
    description="Create a listing for this product: 'Black leather strap chronograph watch, 6800 PKR, water resistant'.",
    expected_output="The product listing in the given format.",
    agent=copywriter,
    output_pydantic=ProductListing,   # <-- structured output
)

result = Crew(agents=[copywriter], tasks=[task]).kickoff()

# 2) Ab result Python object hai
listing = result.pydantic
print("Title   :", listing.title)
print("Price   :", listing.price_pkr, "PKR")
print("Features:", listing.features)
print("Tags    :", ", ".join(listing.tags))

# Dictionary chahiye?
print("\nAs dict:", listing.model_dump())

# ------------------------------------------------------------------
# Agent.kickoff ke saath bhi chalta hai:
#   out = copywriter.kickoff("...", response_format=ProductListing)
#   out.pydantic
# ------------------------------------------------------------------
