"""
=====================================================================
 CLASS 10 | FILE 05: capstone_support_flow.py   (FINAL PROJECT)
=====================================================================
 PROJECT : Watch Store Customer Support System
 Is ek file mein poore course ke concepts saath kaam karte hain:

   Concept                     Kahan use hua
   ------------------------    ----------------------------------------
   Flow + structured state     SupportFlow(Flow[SupportState])
   Structured output           classify() -> Intent (Pydantic)
   Router                      route() -> order_status / product / complaint
   Tool                        lookup_order (@tool)
   Crew inside Flow            product_crew() — Knowledge (RAG) ke saath
   Knowledge                   store_policy.txt + products.csv
   Guardrail                   max_80_words (function guardrail)
   HITL                        @human_feedback -> "send" ya "rewrite"
   Persist                     @persist -> state save hota hai

   classify ─▶ route ─┬─ order_status ─▶ check_order ──┐
                      ├─ product ──────▶ product_crew ─┼─▶ review (HUMAN) ─send─▶ send_reply
                      └─ complaint ────▶ complaint ────┘        │
                                                    ▲──rewrite──┘

 Run:
     uv run python class_10_production/05_capstone_support_flow.py
=====================================================================
"""

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from crewai import Agent, Task, Crew, TaskOutput
from crewai.tools import tool
from crewai.flow import Flow, start, listen, router, or_, persist
from crewai.flow.human_feedback import human_feedback, HumanFeedbackResult
from crewai.knowledge.source.text_file_knowledge_source import TextFileKnowledgeSource
from crewai.knowledge.source.csv_knowledge_source import CSVKnowledgeSource

from llm_setup import get_llm, EMBEDDER

llm = get_llm(temperature=0.2)
KNOWLEDGE_DIR = Path(__file__).parent / "knowledge"

ORDERS = {"1001": "Shipped - TCS tracking 77881", "1002": "Packing - will be dispatched tomorrow"}


# ======================= Building blocks =======================
class Intent(BaseModel):
    category: Literal["order_status", "product", "complaint"] = Field(
        description="order_status = where is my order, product = watch/policy question, complaint = a complaint")
    order_id: str = Field(default="", description="Order number, if the message has one")


@tool("Lookup Order")
def lookup_order(order_id: str) -> str:
    """Returns the order status for an order number."""
    return ORDERS.get(order_id.strip(), "This order number was not found in the system.")


def max_80_words(output: TaskOutput):
    if len(output.raw.split()) > 80:
        return (False, "Make the reply shorter than 80 words — it is a WhatsApp message.")
    return (True, output.raw)


def product_crew() -> Crew:
    expert = Agent(
        role="Watch Product Expert",
        goal="Answer customer questions only from the store's official info",
        backstory="You never make false promises. If the info is not available, you say so clearly.",
        llm=llm,
        knowledge_sources=[
            TextFileKnowledgeSource(file_paths=[KNOWLEDGE_DIR / "store_policy.txt"]),
            CSVKnowledgeSource(file_paths=[KNOWLEDGE_DIR / "products.csv"]),
        ],
        embedder=EMBEDDER,
    )
    task = Task(
        description="Customer WhatsApp message: '{message}'. Write a friendly reply.",
        expected_output="A WhatsApp reply in simple English, under 80 words.",
        agent=expert,
        guardrail=max_80_words,
        guardrail_max_retries=2,
    )
    return Crew(agents=[expert], tasks=[task])


# ======================= The Flow =======================
class SupportState(BaseModel):
    message: str = ""
    category: str = ""
    order_id: str = ""
    draft: str = ""
    sent: bool = False


@persist()
class SupportFlow(Flow[SupportState]):

    @start()
    def classify(self):
        classifier = Agent(role="Message Classifier", goal="Identify the category of customer messages",
                           backstory="You sort the support inbox.", llm=llm)
        result = classifier.kickoff(f"Classify this message: {self.state.message}",
                                    response_format=Intent)
        intent: Intent = result.pydantic
        self.state.category = intent.category
        self.state.order_id = intent.order_id
        print(f"[classify] category={intent.category} order_id='{intent.order_id}'")

    @router(classify)
    def route(self):
        return self.state.category

    @listen("order_status")
    def check_order(self):
        status = lookup_order.run(order_id=self.state.order_id or "unknown")
        self.state.draft = llm.call(
            f"Tell the customer the status of order {self.state.order_id}: '{status}'. "
            "2 lines, simple English, friendly."
        )

    @listen("product")
    def answer_product(self):
        result = product_crew().kickoff(inputs={"message": self.state.message})
        self.state.draft = result.raw

    @listen("complaint")
    def handle_complaint(self):
        self.state.draft = llm.call(
            f"Customer complaint: '{self.state.message}'. Apologize and say the team will call "
            "within 24 hours. 3 lines, simple English."
        )

    # -------- HITL: insaan reply check karega --------
    @human_feedback(
        message="Send this reply to the customer? (Enter = send, or type your changes)",
        emit=["send", "rewrite"],
        llm=llm,
        default_outcome="send",
    )
    @listen(or_(check_order, answer_product, handle_complaint, "rewrite"))
    def review(self):
        last = self.last_human_feedback
        if last and last.outcome == "rewrite":          # pichli dafa changes maange gaye
            self.state.draft = llm.call(
                f"Rewrite this reply according to the feedback.\n"
                f"Reply: {self.state.draft}\nFeedback: {last.feedback}"
            )
        return self.state.draft

    @listen("send")
    def send_reply(self, result: HumanFeedbackResult):
        self.state.sent = True
        print("\n📤 SENT TO CUSTOMER:\n", result.output)
        return "sent"


if __name__ == "__main__":
    print("Customer message likho (ya Enter = sample message):")
    msg = input("> ").strip() or "Is the Black Leather Chrono in stock? And what is the return policy?"

    flow = SupportFlow()
    flow.kickoff(inputs={"message": msg})
    print("\nFinal state:", flow.state.model_dump())
