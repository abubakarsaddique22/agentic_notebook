"""
Step 2: Pehla trace.

Part A: Bina LLM ke — sirf Python functions trace karo (koi paisa nahi lagta).
Part B: Groq LLM call ke saath (OpenAI SDK + Groq URL) — tokens aur cost bhi trace mein aayenge.

Key idea: @traceable lagao -> function ka input, output, time, error sab LangSmith mein.
"""
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


# ---------------- Part A: Plain Python ----------------
@traceable  # bas itna hi! function ka naam run ka naam ban jata hai
def add_tax(price: float) -> float:
    return round(price * 1.17, 2)


@traceable
def checkout(items: list[float]) -> dict:
    subtotal = sum(items)
    total = add_tax(subtotal)  # yeh child run banega (nested)
    return {"subtotal": subtotal, "total_with_tax": total}


# ---------------- Part B: Groq (OpenAI SDK ke zariye) ----------------
# wrap_openai: har call automatically "llm" run ban jati hai (tokens ke saath).
# Groq OpenAI-compatible ha, is liye wahi wrapper kaam karta ha.
openai_client = wrap_openai(OpenAI(base_url=GROQ_BASE_URL, api_key=os.getenv("GROQ_API_KEY")), chat_name="ChatGroq")


@traceable(name="Ask Question")  # custom naam bhi de sakte ho
def ask(question: str) -> str:
    response = openai_client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "You are a helpful assistant. Answer in 2 lines."},
            {"role": "user", "content": question},
        ],
    )
    return response.choices[0].message.content


if __name__ == "__main__":
    print("Part A:", checkout([1000, 2500, 499]))
    print("Part B:", ask("LangSmith kya hai?"))
    print("\nAb smith.langchain.com par jao aur 2 traces dekho: 'checkout' aur 'Ask Question'.")
