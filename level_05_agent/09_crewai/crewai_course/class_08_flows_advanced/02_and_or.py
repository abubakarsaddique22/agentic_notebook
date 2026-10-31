"""
=====================================================================
 CLASS 08 | FILE 02: and_or.py
=====================================================================
 CONCEPT: or_() aur and_() (multiple steps ka intezar)
 Kya hai :
   @listen(and_(a, b)) -> jab a AUR b DONO khatam hon, tab chalo
                          (parallel kaam ka result jama karna)
   @listen(or_(a, b))  -> a YA b, jo bhi pehle khatam ho, chalo

          ┌─▶ fetch_price ──┐
   start ─┤                 ├─ and_ ─▶ make_quote
          └─▶ fetch_stock ──┘

   fast_server ─┐
                ├─ or_ ─▶ use_first_reply
   slow_server ─┘

 Run:
     uv run python class_08_flows_advanced/02_and_or.py
=====================================================================
"""

import time

from crewai.flow import Flow, start, listen, and_, or_


# ================= and_ =================
class QuoteFlow(Flow):

    @start()
    def begin(self):
        print("Quote banana shuru...")

    @listen(begin)
    def fetch_price(self):
        self.state["price"] = 6800
        print("  price mil gayi")

    @listen(begin)
    def fetch_stock(self):
        self.state["stock"] = 4
        print("  stock mil gaya")

    @listen(and_(fetch_price, fetch_stock))     # dono ka intezar
    def make_quote(self):
        msg = f"Price {self.state['price']} PKR, {self.state['stock']} pieces available."
        print("  QUOTE:", msg)
        return msg


QuoteFlow().kickoff()


# ================= or_ =================
class FastestFlow(Flow):

    @start()
    def fast_server(self):
        return "Fast server response"

    @start()                                     # 2 start methods bhi ho sakte hain
    def slow_server(self):
        time.sleep(1)
        return "Slow server response"

    @listen(or_(fast_server, slow_server))       # jo pehle aaye
    def use_first_reply(self, reply):
        print("\nOR result ->", reply)


FastestFlow().kickoff()
