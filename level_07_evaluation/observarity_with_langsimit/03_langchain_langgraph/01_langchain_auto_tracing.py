"""
LangChain automatic tracing.

Koi @traceable nahi — env vars set hain to sab khud trace hoga.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from langchain_core.output_parsers import StrOutputParser  # noqa: E402
# ---------------------------------------------------------
# StrOutputParser  (langchain_core) -- LLM ke message se sirf TEXT nikalta ha
#   chain = prompt | llm | StrOutputParser()  -> trace ma ye bhi alag "parser" run.
# ---------------------------------------------------------
from langchain_core.prompts import ChatPromptTemplate  # noqa: E402
# ---------------------------------------------------------
# ChatPromptTemplate  (langchain_core) -- placeholders wala chat prompt
#   from_messages([("system", "...{var}..."), ("human", "{question}")])
#   .invoke({vars}) -> PromptValue; LangSmith Prompt Hub pe isi ko push / pull karte hain.
# ---------------------------------------------------------
from langchain_groq import ChatGroq  # noqa: E402
# ---------------------------------------------------------
# ChatGroq  (class, langchain-groq) -- Groq ka LangChain chat model
#   LangChain ke andar Groq LLM: chain = prompt | ChatGroq(...) | parser.
#   LangChain runs LangSmith ma KHUD trace hote hain (env vars set hon to).
#   Attributes (constructor):
#     model            -> Groq model id (llama-3.3-70b-versatile, openai/gpt-oss-120b...)
#     temperature      -> 0 = sab se consistent jawab
#     max_tokens       -> jawab ki max lambai (None = model ka default)
#     reasoning_effort -> sirf reasoning models (gpt-oss): "low" | "medium" | "high"
#     reasoning_format -> "parsed" | "raw" | "hidden" -- reasoning kaise wapas aaye
#     timeout, max_retries -> network settings
#     api_key          -> na do to GROQ_API_KEY env var se
#   Methods: .invoke(), .stream(), .bind_tools([...]) (tool calling),
#            .with_structured_output(Schema) (JSON / pydantic output)
# ---------------------------------------------------------
from langsmith import traceable  # noqa: E402
# ---------------------------------------------------------
# traceable  (decorator) -- function ko LangSmith ka "run" (span) bana deta ha
#   Function ka input, output, time, error -- sab trace ma. Andar se doosra
#   @traceable function call ho to wo CHILD run ban jata ha (tree banta ha).
#   Sync, async aur generator -- sab functions pe kaam karta ha.
#   Decorator arguments:
#     name           -> run ka naam (default: function ka naam)
#     run_type       -> "chain" (default) | "llm" | "tool" | "retriever" | "prompt" | "parser"
#                       -- UI isi ke hisaab se run ko dikhata ha (retriever = documents list)
#     tags           -> list of strings, filter karne ke liye
#     metadata       -> dict (version, user_id...), filter + compare ke liye
#     client         -> kaunsa langsmith Client traces bheje (masking / flush ke liye)
#     project_name   -> is function ke runs kis project ma jayen
#     process_inputs / process_outputs -> trace ma jaane se pehle data badlo
#     enabled        -> is function ki tracing on/off
#   Call ke waqt extra: fn(..., langsmith_extra={...})
#     metadata, tags, run_id (apni uuid -- feedback ke liye), project_name,
#     parent, client, name
#   Tracing tabhi hoti ha jab .env ma LANGSMITH_TRACING=true ho.
# ---------------------------------------------------------

MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "You are a polite support agent for a watch store. Reply in {language}."),
        ("human", "{question}"),
    ]
)
llm = ChatGroq(model=MODEL, temperature=0)  # GROQ_API_KEY .env se khud uthata ha

# LCEL chain: prompt -> llm -> parser (har step trace mein alag run)
chain = prompt | llm | StrOutputParser()


@traceable(name="Pre-process")  # traceable aur LangChain mix — ek hi tree mein
def clean(text: str) -> str:
    return text.strip().rstrip("?") + "?"


@traceable(name="Support Pipeline")
def answer(question: str, user_id: str) -> str:
    q = clean(question)
    return chain.invoke(
        {"question": q, "language": "Roman Urdu"},
        config={
            "run_name": "Support Chain",
            "tags": ["langchain", "v1"],
            "metadata": {"user_id": user_id},
        },
    )


if __name__ == "__main__":
    # 1) Direct chain call — automatic trace
    print(chain.invoke({"question": "Return policy kya hai?", "language": "English"}))

    # 2) traceable ke andar chain
    print(answer("  Kya aap Karachi deliver karte ho  ", user_id="user_123"))
