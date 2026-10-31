"""
=====================================================================
 CLASS 03 | FILE 02: hierarchical.py
=====================================================================
 CONCEPT: Process.hierarchical  (Manager wali team)
 Kya hai : CrewAI khud ek "Manager" agent banata hai. Manager:
             1) task parhta hai
             2) faisla karta hai kaunsa agent ye kaam karega (delegation)
             3) jawab check karta hai, zaroorat ho to dobara karwata hai
           Is mein tasks ko agent assign NAHI karte — manager karta hai.
 Zaroori : manager_llm dena lazmi hai.
 Note    : Har step pe manager ki extra LLM call hoti hai -> zyada tokens.

                 [ Manager ]
               /     |      \
        [Coder] [Tester] [Doc Writer]

 Run:
     uv run python class_03_processes/02_hierarchical.py
=====================================================================
"""

from crewai import Agent, Task, Crew, Process

from llm_setup import get_llm

llm = get_llm()

coder = Agent(
    role="Python Developer", 
    goal="Write clean and short Python code",
    backstory="You have been writing Python for 5 years.", 
    llm=llm
    )

tester = Agent(
    role="QA Tester", 
    goal="Find edge cases in the code",
    backstory="You catch every bug.", 
    llm=llm
)
doc_writer = Agent(
    role="Documentation Writer", 
    goal="Write a simple explanation of the code",
    backstory="You write docs for beginners.", 
    llm=llm
)

# NOTE: tasks mein agent= nahi diya — manager khud decide karega
task = Task(
    description=(
        "Write a Python function that checks whether a number is prime. "
        "Then write 3 test cases for it and a 3-line explanation."
    ),
    expected_output="Code + 3 test cases + 3 lines explanation",
)

crew = Crew(
    agents=[coder, tester, doc_writer],
    tasks=[task],
    process=Process.hierarchical,  # <-- manager mode
    manager_llm=llm,               # <-- manager ka dimaag (lazmi)
    verbose=True,
)

print("\n===== FINAL =====\n", crew.kickoff().raw)
