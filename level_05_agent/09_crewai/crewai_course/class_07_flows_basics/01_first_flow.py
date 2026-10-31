"""
=====================================================================
 CLASS 07 | FILE 01: first_flow.py
=====================================================================
 CONCEPT: Flow (Workflow) — @start aur @listen
 Kya hai : Crew = agents khud faisla karte hain (autonomous).
           Flow = AAP step-by-step order fix karte ho (workflow).
           Flow ek Python class hai jis ke methods "steps" hain:
             @start()          -> pehla step (flow yahan se shuru)
             @listen(step_x)   -> jab step_x khatam ho, ye chalo
           Pichle step ka RETURN value agle step ko argument mein
           milta hai.

   generate_number  ──▶  double_it  ──▶  show_result

 Kyun    : Production apps mein control chahiye hota hai — kaunsa step
           kab chalega, data kahan jayega. Flow ye deta hai.
           (Flow ke andar LLM ya poori Crew bhi chala sakte ho — class 08)

 Run:
     uv run python class_07_flows_basics/01_first_flow.py
=====================================================================
"""

import random

from crewai.flow import Flow, start, listen


class NumberFlow(Flow):

    @start()
    def generate_number(self):
        number = random.randint(1, 10)
        print(f"Step 1: random number = {number}")
        return number                       # ye agle step ko jayega

    @listen(generate_number)
    def double_it(self, number):            # pichle step ka return yahan
        doubled = number * 2
        print(f"Step 2: double = {doubled}")
        return doubled

    @listen(double_it)
    def show_result(self, doubled):
        print(f"Step 3: final result = {doubled}")
        return f"Answer: {doubled}"


flow = NumberFlow()
final = flow.kickoff()          # aakhri step ka return value milta hai
print("\nFlow output:", final)

# Flow ka diagram: HTML file banti hai aur browser mein khud khul jati hai
html_path = flow.plot("number_flow.html")
print("Diagram file:", html_path)
