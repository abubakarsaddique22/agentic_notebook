"""
=====================================================================
 CLASS 08 | FILE 07: ai_judge_loop.py
=====================================================================
 CONCEPT: AI Judge Loop (Evaluator-Optimizer pattern)
 Kya hai : Ek AI likhta hai (WRITER), doosra AI check karta hai (JUDGE).
           Judge score + feedback deta hai. Score kam ho to @router
           flow ko WAPAS writer pe bhej deta hai — feedback ke saath.
           Ye loop tab tak chalta hai jab tak judge approve na kare
           ya max attempts poore na hon.

   start ─▶ write_draft ─▶ judge (@router)
                 ▲            ├─ "approved" ─▶ publish
                 └─ "revise" ─┤
                              └─ "give_up"  ─▶ send_to_human (max attempts)

 LangGraph mein isay "evaluator-optimizer" ya reflection loop kehte hain.
 HITL loop (file 04) mein INSAAN check karta tha, yahan AI khud karta hai.

 Run:
     uv run python class_08_flows_advanced/07_ai_judge_loop.py
=====================================================================
"""

from pydantic import BaseModel, Field
from crewai import Agent
from crewai.flow import Flow, start, listen, router, or_

from llm_setup import get_llm

MAX_ATTEMPTS = 3
PASS_SCORE = 8

llm = get_llm()


class Review(BaseModel):
    score: int = Field(description="Quality score from 1 to 10")
    feedback: str = Field(description="What to improve, in 1-2 lines")


class PostState(BaseModel):
    product: str = "Gold Dial Executive watch"
    draft: str = ""
    feedback: str = ""
    score: int = 0
    attempts: int = 0


judge = Agent(
    role="Strict Marketing Editor",
    goal="Score social media posts honestly from 1 to 10",
    backstory="You only give 8+ to posts that are under 50 words, mention the "
              "product name, have a clear call to action and at least 1 hashtag.",
    llm=llm,
)


class JudgeLoopFlow(Flow[PostState]):

    @start()
    def begin(self):
        print("Product:", self.state.product)

    # ---------- WRITER (pehli dafa + har "revise" pe dobara) ----------
    @listen(or_(begin, "revise"))
    def write_draft(self):
        self.state.attempts += 1
        prompt = f"Write an Instagram post (under 50 words) for the '{self.state.product}'."
        if self.state.feedback:
            prompt += (f"\nPrevious draft: {self.state.draft}"
                       f"\nEditor feedback: {self.state.feedback}\nFix these issues.")
        self.state.draft = llm.call(prompt)
        print(f"\n--- Draft {self.state.attempts} ---\n{self.state.draft}")

    # ---------- JUDGE (score dekh ke raasta chunta hai) ----------
    @router(write_draft)
    def judge_draft(self):
        result = judge.kickoff(f"Review this post:\n{self.state.draft}", response_format=Review)
        review: Review = result.pydantic
        self.state.score = review.score
        self.state.feedback = review.feedback
        print(f"[judge] score={review.score}/10 | {review.feedback}")

        if review.score >= PASS_SCORE:
            return "approved"
        if self.state.attempts >= MAX_ATTEMPTS:     # infinite loop se bachao
            return "give_up"
        return "revise"

    @listen("approved")
    def publish(self):
        print(f"\n✅ APPROVED after {self.state.attempts} attempt(s):\n{self.state.draft}")
        return self.state.draft

    @listen("give_up")
    def send_to_human(self):          # NOTE: method ka naam route label jaisa NA rakho
        print(f"\n⚠️ {MAX_ATTEMPTS} attempts ke baad bhi score {self.state.score}. Insaan ko bhejo.")
        return self.state.draft


if __name__ == "__main__":
    flow = JudgeLoopFlow()
    flow.kickoff()
    print("\nFinal state:", flow.state.model_dump(include={"attempts", "score"}))