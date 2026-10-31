"""
=====================================================================
 CLASS 12 | FILE 05: capstone_support_system.py   (FINAL PROJECT)
=====================================================================
 PROJECT : Watch Store Customer Support System
 Poore course ke concepts ek jagah:

   Concept                    Kahan
   -----------------------    -------------------------------------------
   Guardrails                 classifier: PromptInjection + PII masking
   Structured output          classifier -> Intent (Pydantic)
   Workflow + Router          intent ke hisaab se 3 raaste
   Tools                      lookup_order (order raasta)
   Knowledge (RAG)            product raasta: policy + products CSV
   Long-term memory           product agent: user ki pasand yaad
   Session state              workflow: kitne messages handle hue
   HITL (HumanReview)         final reply bhejne se pehle insaan review
                              (reject + feedback = reply dobara likho)
   db                         sab kuch tmp/capstone.db mein save

   classify ─▶ Router ─┬─ order ─────▶ Order Agent (tool) ──────┐
                       ├─ product ───▶ Product Agent (RAG+memory)┼─▶ Final Reply (HUMAN review)
                       └─ complaint ─▶ Complaint Agent ──────────┘

 Run:
     uv run python class_12_production/05_capstone_support_system.py
=====================================================================
"""

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.guardrails import PIIDetectionGuardrail, PromptInjectionGuardrail
from agno.knowledge.knowledge import Knowledge
from agno.run import RunContext
from agno.run.base import RunStatus
from agno.vectordb.lancedb import LanceDb
from agno.workflow import HumanReview, OnReject, Router, Step, StepInput, StepOutput, Workflow

from llm_setup import get_model, get_embedder

KNOWLEDGE_DIR = Path(__file__).parent / "knowledge"
db = SqliteDb(db_file="tmp/capstone.db")

# ======================= Knowledge =======================
knowledge = Knowledge(
    name="store_kb",
    vector_db=LanceDb(uri="tmp/lancedb", table_name="capstone_store", embedder=get_embedder()),
)
knowledge.insert(name="policy", path=str(KNOWLEDGE_DIR / "store_policy.txt"), skip_if_exists=True)
knowledge.insert(name="products", path=str(KNOWLEDGE_DIR / "products.csv"), skip_if_exists=True)

# ======================= Tools =======================
ORDERS = {"1001": "Shipped - TCS tracking 77881", "1002": "Packing - will be dispatched tomorrow"}


def lookup_order(order_id: str) -> str:
    """Returns the order status for an order number."""
    return ORDERS.get(order_id.strip(), "This order number was not found in the system.")


# ======================= Agents =======================
class Intent(BaseModel):
    category: Literal["order", "product", "complaint"] = Field(
        description="order = where is my order, product = watch/policy question, complaint = a complaint")
    order_id: str = Field(default="", description="Order number, if the message has one")


classifier = Agent(
    name="Classifier",
    model=get_model(),
    output_schema=Intent,
    pre_hooks=[PromptInjectionGuardrail(), PIIDetectionGuardrail(mask_pii=True)],
    instructions=["Identify the category of the customer message"],
)

order_agent = Agent(name="Order Agent", model=get_model(), tools=[lookup_order],
                    instructions=["Check the order with the tool and give the status in 2 lines"])

product_agent = Agent(
    name="Product Agent",
    model=get_model(),
    db=db,
    knowledge=knowledge,
    search_knowledge=True,
    update_memory_on_run=True,
    instructions=["Only answer from the store knowledge base", "Remember the customer's preferences"],
)

complaint_agent = Agent(name="Complaint Agent", model=get_model(),
                        instructions=["Apologize, promise a call back within 24 hours, 3 lines"])

reply_agent = Agent(
    name="Reply Writer",
    model=get_model(),
    instructions=["Turn the previous step's answer into a friendly WhatsApp reply",
                  "Simple English, under 60 words, end with '- TimeHouse'"],
)


# ======================= Function steps =======================
def classify(step_input: StepInput, run_context: RunContext) -> StepOutput:
    result = classifier.run(step_input.input)
    run_context.session_state["handled"] += 1

    if result.status == RunStatus.error:                 # guardrail ne roka
        run_context.session_state["blocked"] += 1
        print(f"   [classify] BLOCKED: {result.content}")
        return StepOutput(content="blocked")

    intent: Intent = result.content
    run_context.session_state["last_category"] = intent.category
    print(f"   [classify] {intent.category} | order_id='{intent.order_id}'")
    return StepOutput(content=intent.category)


order_step = Step(name="Order", agent=order_agent)
product_step = Step(name="Product", agent=product_agent)
complaint_step = Step(name="Complaint", agent=complaint_agent)


def blocked_message(step_input: StepInput) -> StepOutput:
    return StepOutput(content="Sorry, this request cannot be processed. Please ask about a watch or an order.")


blocked_step = Step(name="Blocked", executor=blocked_message)


def route(step_input: StepInput) -> list[Step]:
    category = (step_input.previous_step_content or "").strip()
    routes = {"order": order_step, "product": product_step, "complaint": complaint_step}
    return [routes.get(category, blocked_step)]


workflow = Workflow(
    name="TimeHouse Support",
    db=db,
    session_id="support_desk",
    session_state={"handled": 0, "blocked": 0, "last_category": ""},
    steps=[
        Step(name="Classify", executor=classify),
        Router(name="Route", choices=[order_step, product_step, complaint_step, blocked_step], selector=route),
        Step(
            name="Final Reply",
            agent=reply_agent,
            human_review=HumanReview(
                requires_output_review=True,
                output_review_message="Send this reply to the customer?",
                on_reject=OnReject.retry,        # reject + feedback = dobara likho
                max_retries=2,
            ),
        ),
    ],
)


def handle(message: str, user_id: str):
    print(f"\n================ CUSTOMER: {message}")
    run = workflow.run(message, user_id=user_id)

    while run.is_paused:
        for req in run.active_step_requirements:
            print("\nDRAFT REPLY:\n", req.step_output.content if req.step_output else "")
            feedback = input("Enter = bhej do, ya changes likho: ").strip()
            if feedback:
                req.reject(feedback=feedback)
            else:
                req.confirm()
        run = workflow.continue_run(run)

    print("\n📤 SENT:\n", run.content)


if __name__ == "__main__":
    print("Customer ka message likho (Enter = sample message):")
    msg = input("> ").strip() or "Is the Black Leather Chrono in stock? And what is the return policy?"
    handle(msg, user_id="customer_01")
    print("\nDesk stats:", workflow.get_session_state(session_id="support_desk"))
