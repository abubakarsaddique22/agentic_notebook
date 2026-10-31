"""
=====================================================================
 CLASS 07 | FILE 02: flow_state.py
=====================================================================
 CONCEPT: Flow State (steps ke beech shared data)
 Kya hai : self.state ek "shared notebook" hai jo har step parh aur
           likh sakta hai. 2 tareeqe:

   1) Unstructured state -> Flow   ; self.state["key"] = value (dict)
   2) Structured state   -> Flow[MyState] ; Pydantic model, fixed fields
                            + type checking + auto-complete

 Har state ka ek automatic "id" hota hai (self.state.id) — persistence
 (class 08) mein isi se flow resume hota hai.
 kickoff(inputs={...}) se state ki values start mein set kar sakte ho.

 Run:
     uv run python class_07_flows_basics/02_flow_state.py
=====================================================================
"""

from pydantic import BaseModel

from crewai.flow import Flow, start, listen


# ================= 1) UNSTRUCTURED STATE =================
class CounterFlow(Flow):

    @start()
    def step_one(self):
        self.state["count"] = 1
        self.state["log"] = ["step_one done"]

    @listen(step_one)
    def step_two(self):
        self.state["count"] += 1
        self.state["log"].append("step_two done")

    @listen(step_two)
    def step_three(self):
        self.state["count"] += 1
        self.state["log"].append("step_three done")
        return self.state


print("UNSTRUCTURED:", CounterFlow().kickoff())


# ================= 2) STRUCTURED STATE (recommended) =================
class OrderState(BaseModel):
    customer: str = ""
    items: list[str] = []
    total: int = 0
    status: str = "new"


PRICES = {"steel watch": 4500, "leather strap": 1200, "gift box": 500}


class OrderFlow(Flow[OrderState]):          # <-- state ka type batao

    @start()
    def add_items(self):
        # customer ka naam kickoff(inputs=...) se aaya
        print(f"Order for: {self.state.customer}")
        self.state.items = ["steel watch", "gift box"]

    @listen(add_items)
    def calculate_total(self):
        self.state.total = sum(PRICES[i] for i in self.state.items)

    @listen(calculate_total)
    def confirm(self):
        self.state.status = "confirmed"
        return self.state


result = OrderFlow().kickoff(inputs={"customer": "Ahmed"})
print("\nSTRUCTURED:", result)
print("Flow id    :", result.id)
