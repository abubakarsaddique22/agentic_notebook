"""
=====================================================================
 CLASS 02 | FILE 02: task_inputs.py
=====================================================================
 CONCEPT: Dynamic Inputs (placeholders) + Task output settings
 Kya hai :
   {topic} jaise placeholders task/agent ke text mein likho. Phir
   crew.kickoff(inputs={"topic": "..."}) se value bhejo. Ek hi crew
   har dafa naye topic pe chal sakti hai — code badle baghair.

   Task ki extra settings:
     expected_output -> jawab ka format batao (bahut important!)
     output_file     -> jawab file mein save ho jaye
     markdown=True   -> agent ko markdown format mein likhne ko kaho

 Run:
     uv run python class_02_agents_tasks/02_task_inputs.py
=====================================================================
"""

from crewai import Agent, Task, Crew

from llm_setup import get_llm

blogger = Agent(
    role="{topic} Blogger",                       # placeholder agent mein bhi chalta hai
    goal="Write easy blogs about {topic} for beginners",
    backstory="You are a {topic} expert and you write in simple English.",
    llm=get_llm(),
)

blog_task = Task(
    description="Write a short blog about '{topic}'. Audience: {audience}.",
    expected_output="A title, 3 short paragraphs, and 1 tip at the end.",
    agent=blogger,
    markdown=True,                                # markdown headings/bullets
    output_file="outputs/{topic}_blog.md",        # file mein save (folder khud ban jayega)
)

crew = Crew(agents=[blogger], tasks=[blog_task])

# Same crew, 2 alag inputs
for topic in ["Python", "Docker"]:
    result = crew.kickoff(inputs={"topic": topic, "audience": "university students"})
    print(f"\n===== {topic} =====\n{result.raw[:300]}...")

print("\nFiles 'outputs' folder mein save ho gayi hain.")
