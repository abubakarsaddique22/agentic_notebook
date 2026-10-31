"""
=====================================================================
 CLASS 06 | FILE 01: output_schema.py
=====================================================================
 CONCEPT: Structured Output (Pydantic output_schema)
 Kya hai : Normal jawab = free text. Code mein use karne ke liye fix
           format chahiye. Pydantic model banao aur
           Agent(output_schema=MyModel) do.
           Ab result.content ek Python OBJECT hai (string nahi).
 Kyun    : Database mein save, API response, website pe dikhana —
           parsing ka jhanjhat khatam.

 Run:
     uv run python class_06_structured_output_reasoning/01_output_schema.py
=====================================================================
"""

from pydantic import BaseModel, Field

from agno.agent import Agent

from llm_setup import get_model


class ProductListing(BaseModel):
    title: str = Field(description="Catchy product title")
    price_pkr: int = Field(description="Price in PKR")
    features: list[str] = Field(description="3 short features")
    seo_tags: list[str] = Field(description="5 SEO tags")
    in_stock: bool = Field(description="Whether it is in stock")


agent = Agent(
    name="listing_writer",
    model=get_model(),
    description="You create product listings for an e-commerce store.",
    output_schema=ProductListing,          # <-- structured output
)

result = agent.run("Black leather chronograph watch, 6800 PKR, water resistant, 4 pieces available.")
listing: ProductListing = result.content   # Python object

print("Title    :", listing.title)
print("Price    :", listing.price_pkr)
print("Features :", listing.features)
print("Tags     :", ", ".join(listing.seo_tags))
print("In stock :", listing.in_stock)
print("\nAs dict  :", listing.model_dump())
