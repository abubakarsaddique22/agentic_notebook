"""
=====================================================================
 CLASS 10 | FILE 04: test_and_train.py
=====================================================================
 CONCEPT: Testing (evaluation) + Training
 TEST  : crew.test(n_iterations, eval_llm) -> crew ko N dafa chalata hai,
         ek "judge" LLM har task ko 1-10 score deta hai aur table
         print karta hai. Prompt badalne ke baad check karo — quality
         behtar hui ya kharab?
 TRAIN : crew.train(n_iterations, filename, inputs) -> har run ke baad
         AAP feedback dete ho (HITL). CrewAI aap ka feedback file mein
         save karta hai aur agli dafa agents usay "seekh" ke use karte
         hain. Terminal: `crewai train -n 3`

 Note  : Training mein HAR dafa kuch feedback zaroor likho (khali Enter
         na dabao) — warna "Missing fields (human_feedback)" error aata hai.
         Test ke dauran "Sync handler error in on_crew_test_result" dikhe
         to ignore karo — CrewAI ki apni telemetry ka chhota bug hai,
         score table phir bhi sahi aati hai.

 Run:
     uv run python class_10_production/04_test_and_train.py          (sirf test)
     uv run python class_10_production/04_test_and_train.py train    (train bhi)
=====================================================================
"""

import sys

from crewai import Agent, Task, Crew

from llm_setup import get_llm

llm = get_llm()

writer = Agent(role="Product Description Writer", goal="Write descriptions that sell",
               backstory="You are an e-commerce copy expert.", llm=llm)

task = Task(description="Write a 50-word product description for '{product}'.",
            expected_output="50 words, 1 paragraph", agent=writer)

crew = Crew(agents=[writer], tasks=[task])
inputs = {"product": "Sports Silicone Strap Watch"}

# ---------- TEST ----------
print("===== TESTING (2 runs) =====")
crew.test(n_iterations=2, eval_llm=llm, inputs=inputs)

# ---------- TRAIN (optional) ----------
if len(sys.argv) > 1 and sys.argv[1] == "train":
    print("\n===== TRAINING =====")
    print("Har run ke baad apna feedback likho (e.g. 'price bhi likho').")
    crew.train(n_iterations=2, filename="outputs/trained_agents.pkl", inputs=inputs)
    print("Training data saved: outputs/trained_agents.pkl")
    # Trained data use karna:  Crew(..., trained_agents_file="outputs/trained_agents.pkl")
