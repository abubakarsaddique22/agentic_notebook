"""
=====================================================================
 CLASS 08 | FILE 05: persist_resume.py
=====================================================================
 CONCEPT: @persist (Flow state ko save karna + resume karna)
 Kya hai : @persist class ke upar lagao. Har step ke baad flow ka
           state database (SQLite, aapke PC pe) mein save hota hai.
           Baad mein same "id" de ke flow chalao to purana state wapas
           load ho jata hai — jaise game ka "save point".
 Kyun    : Lambe workflows, server restart, ya HITL jahan insaan ka
           jawab ghanton baad aaye — kaam zaya nahi hota.

 Is file mein:
   Run 1: naya cart, 1 item add
   Run 2: same id ke saath — pichla item yaad hai, naya add hota hai

 Run:
     uv run python class_08_flows_advanced/05_persist_resume.py
=====================================================================
"""

from pydantic import BaseModel

from crewai.flow import Flow, start, listen, persist


class CartState(BaseModel):
    items: list[str] = []
    visits: int = 0


@persist()                       # <-- poora flow persist hoga
class CartFlow(Flow[CartState]):

    @start()
    def open_cart(self):
        self.state.visits += 1
        print(f"Visit #{self.state.visits} | cart mein pehle se: {self.state.items}")

    @listen(open_cart)
    def add_item(self):
        new_item = f"watch_{len(self.state.items) + 1}"
        self.state.items.append(new_item)
        print("Added:", new_item)
        return self.state.items


# ---------- Run 1 (naya flow) ----------
flow1 = CartFlow()
flow1.kickoff()
saved_id = flow1.state.id
print("Saved flow id:", saved_id)

# ---------- Run 2 (resume with same id) ----------
print("\n--- Resume kar rahe hain ---")
flow2 = CartFlow()
flow2.kickoff(inputs={"id": saved_id})      # <-- id do, state load ho jayega
print("Cart ab:", flow2.state.items)
