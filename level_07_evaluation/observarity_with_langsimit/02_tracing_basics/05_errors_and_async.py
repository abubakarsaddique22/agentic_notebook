"""
1. Errors: exception aaye to run laal (error) mark hota hai + stack trace save hota hai.
   Production debugging ka sabse bara faida yahi hai.
2. Async: @traceable async functions par bhi kaam karta hai. Parallel calls bhi
   sahi parent ke neeche nest hoti hain.
"""
import asyncio
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
from openai import AsyncOpenAI  # noqa: E402
# ---------------------------------------------------------
# AsyncOpenAI  (class) -- OpenAI SDK ka ASYNC client (yahan Groq URL ke saath)
#   await client.chat.completions.create(...) -- asyncio.gather se kai calls
#   parallel chal sakti hain. wrap_openai isay bhi wrap karta ha.
# ---------------------------------------------------------

# Groq OpenAI-compatible endpoint -- OpenAI SDK hi use hota ha, sirf URL + key Groq ki
GROQ_BASE_URL = "https://api.groq.com/openai/v1"
MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
aclient = wrap_openai(AsyncOpenAI(base_url=GROQ_BASE_URL, api_key=os.getenv("GROQ_API_KEY")), chat_name="ChatGroq")


# ---------- 1) Errors ----------
@traceable(run_type="tool", name="Payment Gateway")
def charge_card(amount: int) -> str:
    if amount > 10000:
        raise RuntimeError("Gateway timeout: amount too large")
    return "charged"


@traceable(name="Checkout With Error")
def checkout(amount: int) -> str:
    try:
        return charge_card(amount)
    except RuntimeError:
        # Child run error mein hoga, parent fallback ke saath success
        return "fallback: COD selected"


# ---------- 2) Async + parallel ----------
@traceable(name="Translate")
async def translate(text: str, lang: str) -> str:
    resp = await aclient.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": f"Translate to {lang}, only output translation: {text}"}],
    )
    return resp.choices[0].message.content


@traceable(name="Translate To Many")
async def translate_many(text: str) -> dict:
    langs = ["Urdu", "Arabic", "French"]
    results = await asyncio.gather(*(translate(text, l) for l in langs))
    return dict(zip(langs, results))


if __name__ == "__main__":
    print(checkout(500))
    print(checkout(50000))  # UI mein child run laal dikhega
    print(asyncio.run(translate_many("Your order has been shipped.")))
    print("UI: 'Translate To Many' trace mein 3 parallel children, timeline view dekho.")
