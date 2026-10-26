"""
Jis app ko hum evaluate karenge — chhota sa FAQ support bot.

Do prompt versions:
  v1 — simple, loose (zyada lamba, off-topic bhi jawab de deta hai)
  v2 — strict (sirf FAQ se, short, off-topic politely mana)

Evaluation se hum SABIT karenge ke v2 behtar hai — andaze se nahi.
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
client = wrap_openai(OpenAI(base_url=GROQ_BASE_URL, api_key=os.getenv("GROQ_API_KEY")), chat_name="ChatGroq")

FAQ = """
- Delivery: Lahore mein 1-2 din, baqi Pakistan mein 3-5 working days.
- Delivery charges: Rs. 3000 se upar order par free, warna Rs. 200.
- Payment: Sirf Cash on Delivery (COD). Online/card/crypto payment nahi hoti.
- Exchange: Delivery ke 7 din ke andar, product unused ho to exchange ho sakta hai. Refund nahi.
- Warranty: Watch machine par 6 mahine ki warranty.
"""

PROMPTS = {
    "v1": "You are a helpful assistant for a watch store. Here is some info:\n{faq}",
    "v2": (
        "You are the customer support agent of a watch store.\n"
        "Rules:\n"
        "1. Answer ONLY using the FAQ below. If the answer is not in the FAQ, say you can only help "
        "with store-related questions.\n"
        "2. Reply in Roman Urdu, maximum 2 short sentences.\n"
        "3. Never invent prices, policies or payment methods.\n\n"
        "FAQ:\n{faq}"
    ),
}


@traceable(name="Support Bot")
def support_bot(question: str, prompt_version: str = "v2") -> str:
    system = PROMPTS[prompt_version].format(faq=FAQ)
    resp = client.chat.completions.create(
        model=MODEL,
        temperature=0,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": question}],
    )
    return resp.choices[0].message.content


if __name__ == "__main__":
    print(support_bot("Bitcoin se payment ho sakti hai?", "v1"))
    print(support_bot("Bitcoin se payment ho sakti hai?", "v2"))
