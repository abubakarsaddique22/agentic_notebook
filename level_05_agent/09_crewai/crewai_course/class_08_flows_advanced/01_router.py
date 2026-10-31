"""
=====================================================================
 CLASS 08 | FILE 01: router.py
=====================================================================
 CONCEPT: @router (Flow mein if/else — branching)
 Kya hai : Router step ek STRING label return karta hai. Jis listener
           ne @listen("wahi_label") likha hai, sirf wahi chalega.

                         ┌──"complaint"──▶ handle_complaint
   classify (router) ────┼──"order"──────▶ handle_order
                         └──"general"────▶ handle_general

 Kyun    : Customer support, approvals, payment status — har jagah
           "agar ye ho to wahan jao" wali logic chahiye hoti hai.
 Is file mein classification LLM karta hai, routing Python.

 Run:
     uv run python class_08_flows_advanced/01_router.py
=====================================================================
"""

from pydantic import BaseModel

from crewai.flow import Flow, start, listen, router

from llm_setup import get_llm

llm = get_llm(temperature=0.0)


class SupportState(BaseModel):
    message: str = ""
    category: str = ""
    reply: str = ""


class SupportFlow(Flow[SupportState]):

    @start()
    def receive(self):
        print("Customer:", self.state.message)

    @router(receive)
    def classify(self):
        answer = llm.call(
            "Classify this message in only ONE word: complaint, order, or general.\n"
            f"Message: {self.state.message}\nOnly write the word."
        ).strip().lower()

        # LLM kabhi extra text de de, isliye safe check
        for label in ["complaint", "order"]:
            if label in answer:
                self.state.category = label
                return label
        self.state.category = "general"
        return "general"

    @listen("complaint")
    def handle_complaint(self):
        self.state.reply = "Sorry! Your complaint has been registered, you will get a call within 24 hours."
        return self.state.reply

    @listen("order")
    def handle_order(self):
        self.state.reply = "Thank you! To place an order, please send your name, address and the watch name."
        return self.state.reply

    @listen("general")
    def handle_general(self):
        self.state.reply = llm.call(f"As a store assistant, reply in 1 line: {self.state.message}")
        return self.state.reply


messages = [
    "My watch stopped working in 2 days, very bad experience!",
    "I want to order the Gold Dial Executive",
    "Which city is your shop in?",
]

for msg in messages:
    flow = SupportFlow()
    flow.kickoff(inputs={"message": msg})
    print(f"--> [{flow.state.category}] {flow.state.reply}\n")
