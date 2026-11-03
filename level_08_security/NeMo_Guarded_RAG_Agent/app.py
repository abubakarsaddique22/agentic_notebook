"""Original LangChain tool-calling RAG agent, now wrapped by NeMo rails.

No baseline mode: the only supported entry point is guardrailed.
"""
import argparse
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent / ".env")

from langchain_core.runnables import RunnableLambda
from nemoguardrails import RailsConfig
from nemoguardrails.integrations.langchain.runnable_rails import RunnableRails
from agent.runtime import ask_agent
from agent.identity import Principal, set_principal, reset_principal


@lru_cache(maxsize=1)
def guarded_agent():
    """NeMo routes user/dialog/output rails around the *original* RAG agent."""
    config = RailsConfig.from_path(str(Path(__file__).resolve().parent / "config"))
    chain = RunnableLambda(lambda payload: {"output": ask_agent(payload["input"])})
    return RunnableRails(
        config=config,
        runnable=chain,
        input_key="input",
        output_key="output",
        passthrough=True,
    )


def handle(message: str, principal: Principal | None = None) -> str:
    token = set_principal(principal or Principal("anonymous", "viewer"))
    try:
        result = guarded_agent().invoke({"input": message})
    finally:
        reset_principal(token)
    return str(result.get("output", result)) if isinstance(result, dict) else str(result)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--role", choices=["viewer", "operator"], default="viewer")
    parser.add_argument("--user-id", default="anonymous")
    parser.add_argument("--once", help="Run one prompt and exit")
    args = parser.parse_args()
    principal = Principal(args.user_id, args.role)
    if args.once:
        print(handle(args.once, principal))
        return
    print("NeMo Guarded Agentic RAG ready | type exit to quit")
    while True:
        try:
            question = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            break
        if question.lower() in {"exit", "quit"}:
            break
        if not question:
            continue
        try:
            print("Assistant:", handle(question, principal))
        except Exception as exc:
            print("ERROR:", type(exc).__name__, str(exc))


if __name__ == "__main__":
    main()
