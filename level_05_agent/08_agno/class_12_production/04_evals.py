"""
=====================================================================
 CLASS 12 | FILE 04: evals.py
=====================================================================
 CONCEPT: Evals (agent ki quality NAAPNA)
 Kya hai : Prompt ya model badla — agent behtar hua ya kharab? Andaze
           ki bajaye test karo:
   AccuracyEval    -> expected jawab se milao. Ek "judge" model 1-10
                      score deta hai.
   ReliabilityEval -> kya agent ne SAHI TOOL call kiya?
   PerformanceEval -> kitna time / memory laga (speed test)
 Kyun    : Production se pehle aur har change ke baad chalao (jaise
           software ke unit tests).

 Run:
     uv run python class_12_production/04_evals.py
=====================================================================
"""

from agno.agent import Agent
from agno.eval.accuracy import AccuracyEval
from agno.eval.reliability import ReliabilityEval
from agno.tools.calculator import CalculatorTools

from llm_setup import get_model

math_agent = Agent(
    name="math_agent",
    model=get_model(),
    tools=[CalculatorTools()],
    instructions=["Use the calculator tool for math", "Only write the final number"],
)

# ---------- 1) Accuracy ----------
accuracy = AccuracyEval(
    name="Watch bill accuracy",
    agent=math_agent,
    model=get_model(),                       # judge model
    input="3 watches at 4500 each and 2 straps at 1200 each — what is the total?",
    expected_output="15900",
    num_iterations=1,
)
accuracy_result = accuracy.run(print_results=True)
if accuracy_result:
    print("Average score:", accuracy_result.avg_score)

# ---------- 2) Reliability (sahi tool call hua?) ----------
response = math_agent.run("Multiply 12 by 15")
reliability = ReliabilityEval(
    name="Calculator used",
    agent_response=response,
    expected_tool_calls=["multiply"],
)
reliability_result = reliability.run(print_results=True)
if reliability_result:
    print("Reliability:", reliability_result.eval_status)
