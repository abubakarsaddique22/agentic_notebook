"""
LangChain + Langfuse CallbackHandler.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from langchain_core.output_parsers import StrOutputParser  # noqa: E402
from langchain_core.prompts import ChatPromptTemplate  # noqa: E402
from langchain_openai import ChatOpenAI  # noqa: E402
from langfuse import get_client, observe, propagate_attributes  # noqa: E402
from langfuse.langchain import CallbackHandler  # noqa: E402

MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
langfuse = get_client()

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "You are a polite support agent for a watch store. Reply in {language}."),
        ("human", "{question}"),
    ]
)
llm = ChatOpenAI(model=MODEL, temperature=0)
chain = prompt | llm | StrOutputParser()  # har step trace mein alag observation


# ---------- Tareeqa 1: direct chain call + metadata keys ----------
def direct_call() -> str:
    handler = CallbackHandler()
    return chain.invoke(
        {"question": "Return policy kya hai?", "language": "English"},
        config={
            "callbacks": [handler],
            "run_name": "support-chain",
            "metadata": {
                "langfuse_user_id": "user_123",
                "langfuse_session_id": "session-lc-1",
                "langfuse_tags": ["langchain", "v1"],
            },
        },
    )


# ---------- Tareeqa 2: @observe ke andar (industry pattern) ----------
@observe(name="pre-process")
def clean(text: str) -> str:
    return text.strip().rstrip("?") + "?"


@observe(name="support-pipeline")
def answer(question: str, user_id: str) -> str:
    with propagate_attributes(user_id=user_id, tags=["langchain", "pipeline"]):
        q = clean(question)
        handler = CallbackHandler()  # current trace ke andar nest hoga
        return chain.invoke({"question": q, "language": "Roman Urdu"}, config={"callbacks": [handler]})


if __name__ == "__main__":
    print("1)", direct_call())
    print("2)", answer("  Kya aap Karachi deliver karte ho  ", user_id="user_456"))
    langfuse.flush()
