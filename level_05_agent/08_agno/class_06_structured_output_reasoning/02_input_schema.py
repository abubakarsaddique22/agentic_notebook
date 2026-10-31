"""
=====================================================================
 CLASS 06 | FILE 02: input_schema.py
=====================================================================
 CONCEPT: Structured Input (input_schema)
 Kya hai : Jaise output ka format fix kiya, waise INPUT ka bhi.
           Agent(input_schema=MyModel) -> agent sirf us shape ka input
           lega. Galat input -> foran error (LLM call se pehle!).
 Kyun    : Jab agent API / doosre system se data leta hai, to ghalat
           ya adhoora data pehle hi pakra jaye.

 Run:
     uv run python class_06_structured_output_reasoning/02_input_schema.py
=====================================================================
"""

from pydantic import BaseModel, Field

from agno.agent import Agent

from llm_setup import get_model


class ReviewRequest(BaseModel):
    product: str
    rating: int = Field(ge=1, le=5, description="1 to 5 stars")
    customer_comment: str


class ReviewReply(BaseModel):
    sentiment: str = Field(description="positive / negative / neutral")
    reply: str = Field(description="A 2-line reply to the customer")


agent = Agent(
    name="review_responder",
    model=get_model(),
    input_schema=ReviewRequest,      # <-- input ka format
    output_schema=ReviewReply,       # <-- output ka format
    instructions=["For a negative review, apologize and offer a solution"],
)

# ---------- Sahi input ----------
request = ReviewRequest(product="Classic Steel", rating=2, customer_comment="The strap broke within 1 week")
result = agent.run(input=request)
print("Sentiment:", result.content.sentiment)
print("Reply    :", result.content.reply)

# ---------- Galat input (rating 9) ----------
try:
    ReviewRequest(product="X", rating=9, customer_comment="...")
except Exception as e:
    print("\nGalat input pakra gaya:", type(e).__name__)
