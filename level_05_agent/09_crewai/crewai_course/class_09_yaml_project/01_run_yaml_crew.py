"""
=====================================================================
 CLASS 09 | FILE 01: run_yaml_crew.py
=====================================================================
 CONCEPT: YAML-based Crew project chalana
 Kya hai : watch_review_crew/ folder mein official project structure:
             config/agents.yaml  -> agents ki details
             config/tasks.yaml   -> tasks ki details
             crew.py             -> @CrewBase class (Python wiring)
           Ye file sirf us crew ko import karke chalati hai.
           Asal project mein yahi kaam `crewai run` command karti hai.

 Run:
     uv run python class_09_yaml_project/01_run_yaml_crew.py
=====================================================================
"""

from watch_review_crew.crew import WatchReviewCrew

inputs = {"product": "Black Leather Chronograph", "price": "6800"}

result = WatchReviewCrew().crew().kickoff(inputs=inputs)

print("\n===== REVIEW =====\n", result.raw)
