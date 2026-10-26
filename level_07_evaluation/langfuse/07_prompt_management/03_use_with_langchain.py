"""
Langfuse prompt ko LangChain mein use karna.

get_langchain_prompt(): Langfuse ke {{var}} ko LangChain ke {var} mein badal deta hai.
Link: LangChain prompt template ke metadata mein {"langfuse_prompt": prompt}
      (sirf PromptTemplate par lagao, LLM par nahi)
"""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from langchain_core.prompts import ChatPromptTemplate  # noqa: E402
from langchain_openai import ChatOpenAI  # noqa: E402
from langfuse import get_client  # noqa: E402
from langfuse.langchain import CallbackHandler  # noqa: E402

langfuse = get_client()

if __name__ == "__main__":
    lf_prompt = langfuse.get_prompt("watch-support", type="chat")  # production label

    lc_prompt = ChatPromptTemplate.from_messages(lf_prompt.get_langchain_prompt())
    lc_prompt.metadata = {"langfuse_prompt": lf_prompt}  # generation <-> prompt version link

    config = lf_prompt.config or {}
    llm = ChatOpenAI(
        model=config.get("model", os.getenv("OPENAI_MODEL", "gpt-4o-mini")),
        temperature=config.get("temperature", 0),
    )
    chain = lc_prompt | llm

    result = chain.invoke(
        {
            "store_name": "Watch Store",
            "faq": "Sirf COD. 7 din exchange. 6 mahine warranty.",
            "question": "Warranty kitni hai?",
        },
        config={"callbacks": [CallbackHandler()]},
    )
    print(result.content)
    langfuse.flush()
