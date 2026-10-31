"""
=====================================================================
 CLASS 07 | FILE 03: flow_with_ai.py
=====================================================================
 CONCEPT: Flow ke steps mein AI use karna (LLM + Agent)
 Kya hai : Flow ka har step normal Python hai — to us mein:
             - seedha LLM call (llm.call)        -> chhota, sasta kaam
             - akela Agent (agent.kickoff)        -> tools/reasoning wala kaam
             - poori Crew (crew.kickoff)          -> team wala kaam (class 08)
           Yahi CrewAI ka "production pattern" hai: Flow control rakhta
           hai, AI sirf wahan jahan zaroorat hai.

   pick_topic (LLM) ──▶ write_post (Agent) ──▶ save_post (Python)

 Run:
     uv run python class_07_flows_basics/03_flow_with_ai.py
=====================================================================
"""

from pathlib import Path

from pydantic import BaseModel

from crewai import Agent
from crewai.flow import Flow, start, listen

from llm_setup import get_llm

llm = get_llm()


class PostState(BaseModel):
    niche: str = "watches"
    topic: str = ""
    post: str = ""


class BlogPostFlow(Flow[PostState]):

    @start()
    def pick_topic(self):
        # Step 1: seedha LLM call (agent ki zaroorat nahi)
        self.state.topic = llm.call(
            f"Give one blog topic for the '{self.state.niche}' niche. Only write the topic, 1 line."
        ).strip()
        print("Topic:", self.state.topic)

    @listen(pick_topic)
    def write_post(self):
        # Step 2: Agent se kaam
        writer = Agent(
            role="Blog Writer",
            goal="Write simple and useful blog posts",
            backstory="You write for beginners.",
            llm=llm,
        )
        result = writer.kickoff(f"Write a 100-word post on this topic: {self.state.topic}")
        self.state.post = result.raw

    @listen(write_post)
    def save_post(self):
        # Step 3: normal Python
        out = Path("outputs") / "flow_post.md"
        out.parent.mkdir(exist_ok=True)
        out.write_text(f"# {self.state.topic}\n\n{self.state.post}", encoding="utf-8")
        return f"Saved to {out}"


flow = BlogPostFlow()
print(flow.kickoff(inputs={"niche": "men's watches"}))
print("\nPOST:\n", flow.state.post)
