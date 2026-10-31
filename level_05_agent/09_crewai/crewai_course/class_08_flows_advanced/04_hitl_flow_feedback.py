"""
=====================================================================
 CLASS 08 | FILE 04: hitl_flow_feedback.py
=====================================================================
 CONCEPT: HITL in Flows — @human_feedback (approve / reject / revise)
 Kya hai : Flow ke kisi step pe @human_feedback lagao. Step khatam hone
           ke baad output aap ko dikhaya jata hai aur aap ka feedback
           liya jata hai.
             emit=[...]  -> aap ka free text (e.g. "theek hai, chala do")
                            LLM ek label mein badal deta hai:
                            "approved" / "rejected" / "needs_revision"
             Phir @listen("approved") wala step chalta hai.
 Loop    : "needs_revision" aaye to draft dobara likha jata hai —
           jab tak aap approve ya reject na karo.

   write_draft ──▶ review (HUMAN) ──approved────▶ publish
        ▲               │
        └─needs_revision┘──rejected─────▶ discard

 Run:
     uv run python class_08_flows_advanced/04_hitl_flow_feedback.py
=====================================================================
"""

from pydantic import BaseModel

from crewai.flow import Flow, start, listen, or_
from crewai.flow.human_feedback import human_feedback, HumanFeedbackResult

from llm_setup import get_llm

llm = get_llm()


class PostState(BaseModel):
    product: str = "Minimal White Dial watch"
    draft: str = ""
    attempts: int = 0


class ApprovalFlow(Flow[PostState]):

    @start()
    def start_flow(self):
        print("Product:", self.state.product)

    @human_feedback(
        message="Is this Facebook post okay? (approve / reject / or type your changes)",
        emit=["approved", "rejected", "needs_revision"],
        llm=llm,                              # feedback -> label
        default_outcome="approved",           # sirf Enter = approved
    )
    @listen(or_(start_flow, "needs_revision"))  # revision pe dobara chalega
    def write_draft(self):
        self.state.attempts += 1
        feedback = ""
        if self.last_human_feedback:          # pichla feedback (agar hai)
            feedback = f"Previous feedback: {self.last_human_feedback.feedback}"
        self.state.draft = llm.call(
            f"Write a 40-word Facebook post for '{self.state.product}'. {feedback}"
        )
        return self.state.draft               # yahi human ko dikhega

    @listen("approved")
    def publish(self, result: HumanFeedbackResult):
        print(f"\nPUBLISHED (attempt {self.state.attempts}):\n{result.output}")
        return "published"

    @listen("rejected")
    def discard(self, result: HumanFeedbackResult):
        print("\nPost reject ho gayi. Reason:", result.feedback)
        return "discarded"


flow = ApprovalFlow()
print("Final status:", flow.kickoff())

print("\nFeedback history:")
for fb in flow.human_feedback_history:
    print(f"  - outcome={fb.outcome} | feedback='{fb.feedback}'")
