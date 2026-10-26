"""Red teaming with DeepTeam (the roadmap's named framework), using Ollama.

DeepTeam is from Confident AI, the same team as DeepEval (which you used in
Level 7). It auto-generates adversarial inputs for 50+ vulnerability types and
measures how your app handles them. We point its attacker/judge at your local
Ollama model, so there is no OpenAI key and no cost.

Setup (Windows PowerShell):
    pip install deepteam
    deepeval set-ollama --model gpt-oss:20b-cloud      # attacker/judge via Ollama
    python -m m8_7_red_teaming.deepteam_redteam

Note: DeepTeam fires many model calls. Keep the vulnerability/attack list small
while learning. It targets our SECURE agent through a model_callback.
"""
from __future__ import annotations


def model_callback(user_input: str) -> str:
    """Wrap the secure agent so DeepTeam can attack it as a black box."""
    from app.agent import message_text
    from m8_9_capstone.secure_agent import build_secure_agent, secure_turn

    agent = build_secure_agent()
    # turn off the model-based guard inside so we don't nest heavy Llama Guard calls;
    # rails + code defences still apply. Flip to True for a full-stack test.
    res = secure_turn(agent, user_input, use_model_guard=False)
    return message_text(res["messages"][-1])


def main() -> None:
    try:
        # red_team: DeepTeam ka main function. Yeh khud attack messages banata hai,
        #           aap ke agent par chalata hai, aur score deta hai ke agent bacha ya nahi.
        from deepteam import red_team
        # vulnerabilities: kaunsi kamzori test karni hai.
        #   PromptLeakage = agent apna system prompt / secret to nahi ugal raha?
        #   PIILeakage    = agent kisi ki zaati maloomat (naam/phone/email) to leak nahi kar raha?
        from deepteam.vulnerabilities import PromptLeakage, PIILeakage
        # attacks: hamla kis tareeqe se karna hai.
        #   PromptInjection = "apne instructions bhool jao" type ke injected messages.
        from deepteam.attacks.single_turn import PromptInjection
    except ImportError:
        print("deepteam not installed. Run: pip install deepteam")
        print("Then: deepeval set-ollama --model gpt-oss:20b-cloud")
        return

    risk = red_team(
        model_callback=model_callback,
        vulnerabilities=[PromptLeakage(), PIILeakage()],
        attacks=[PromptInjection()],
    )
    print(risk)


if __name__ == "__main__":
    main()
