"""
wrap_openai — OpenAI SDK ki automatic tracing (yahan Groq ke saath:
Groq OpenAI-compatible API deta ha, to OpenAI SDK + Groq base_url = same tracing).

Seekho:
  1. Normal call (tokens automatically)
  2. Streaming call (stream bhi trace hota hai)
  3. JSON output wala call
  4. Wrapper ko traceable pipeline ke andar use karna
"""
import json
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

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
from langsmith.wrappers import wrap_openai  # noqa: E402
# ---------------------------------------------------------
# wrap_openai  (function) -- OpenAI SDK client ki AUTOMATIC tracing
#   wrap_openai(client) ek naya client deta ha jis ki har chat.completions.create
#   call khud "llm" run ban jati ha: messages, model, tokens, latency, streaming.
#   Groq ka apna LangSmith wrapper nahi ha -- lekin Groq OpenAI-compatible ha,
#   is liye OpenAI SDK (base_url = Groq) + wrap_openai = poori tracing.
#   Arguments:
#     client        -> OpenAI() ya AsyncOpenAI() object
#     chat_name     -> trace ma LLM run ka naam (default "ChatOpenAI"; yahan "ChatGroq")
#     tracing_extra -> {"metadata", "tags", "client"} -- har call pe lagne wali extra info
#   NOTE: tokens hamesha dikhte hain; COST tabhi jab LangSmith ke Settings ->
#   Model Pricing ma Groq model ka rate add karo (warna $0 dikhega).
# ---------------------------------------------------------
from openai import OpenAI  # noqa: E402
# ---------------------------------------------------------
# OpenAI  (class) -- OpenAI ka Python SDK, lekin yahan GROQ ke liye use ho raha ha
#   Groq ka API OpenAI jaisa ha, is liye sirf do cheezein badalni hain:
#     base_url = "https://api.groq.com/openai/v1"
#     api_key  = GROQ_API_KEY  (.env se)
#   Baqi sab same: client.chat.completions.create(model=..., messages=[...])
#   Groq pe na chalne wale parameters: logprobs, logit_bias, top_logprobs, n>1.
#   temperature=0 Groq khud 1e-8 kar deta ha (koi masla nahi).
# ---------------------------------------------------------

# Groq OpenAI-compatible endpoint -- OpenAI SDK hi use hota ha, sirf URL + key Groq ki
GROQ_BASE_URL = "https://api.groq.com/openai/v1"
MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

# Client ek dafa wrap karo, poori app mein yahi use karo (industry pattern)
client = wrap_openai(OpenAI(base_url=GROQ_BASE_URL, api_key=os.getenv("GROQ_API_KEY")), chat_name="ChatGroq")


def normal_call() -> str:
    # traceable ke bina bhi yeh call apna khud ka trace banayegi
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": "Ek line mein: observability kya hai?"}],
    )
    return resp.choices[0].message.content


def streaming_call() -> str:
    # include_usage=True dene se streaming mein bhi tokens count hote hain
    stream = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": "3 watch brands ke naam batao."}],
        stream=True,
        stream_options={"include_usage": True},
    )
    full = ""
    for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            piece = chunk.choices[0].delta.content
            full += piece
            print(piece, end="", flush=True)
    print()
    return full


@traceable(name="Extract Order Info", run_type="chain")
def extract_order_info(customer_text: str) -> dict:
    """LLM se structured JSON nikalna — real projects mein bohat common."""
    resp = client.chat.completions.create(
        model=MODEL,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": 'Extract JSON: {"product": str, "quantity": int, "city": str}',
            },
            {"role": "user", "content": customer_text},
        ],
    )
    return json.loads(resp.choices[0].message.content)


if __name__ == "__main__":
    print("1)", normal_call())
    print("2) Streaming:")
    streaming_call()
    print("3)", extract_order_info("Mujhe 2 black watches chahiye, Lahore delivery"))
    print("\nUI mein LLM run kholo -> 'Messages' view, tokens aur cost dekho.")
