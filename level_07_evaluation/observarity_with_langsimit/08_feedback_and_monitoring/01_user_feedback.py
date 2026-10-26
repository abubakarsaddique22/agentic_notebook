"""
User feedback ko trace ke saath jorna.

Steps:
  1. Request aate hi run_id (uuid) khud banao
  2. langsmith_extra={"run_id": run_id} se trace ko wahi ID do
  3. run_id frontend/WhatsApp ko response ke saath bhejo
  4. User 👍/👎 kare -> client.create_feedback(run_id, ...)
"""
import os
import uuid
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from langsmith import Client, traceable  # noqa: E402
# ---------------------------------------------------------
# Client  (class) -- LangSmith API se baat karne wala object
#   Client() .env se LANGSMITH_API_KEY / LANGSMITH_ENDPOINT khud uthata ha.
#   Constructor options: api_key, api_url, hide_inputs / hide_outputs (masking
#   function ya True), anonymizer, auto_batch_tracing (default True).
#   Is project ma use hone wale methods:
#     list_projects()                         -> projects ki list
#     list_runs(project_name, is_root, error, start_time, filter, limit) -> traces query
#     has_dataset / read_dataset / create_dataset(dataset_name, description)
#     create_examples(dataset_id, examples=[{inputs, outputs, metadata, split}])
#     list_examples(dataset_name, splits=[...], as_of="prod")  -> examples parho
#     update_dataset_tag(dataset_name, as_of=datetime, tag)   -> version ko tag
#     evaluate(target, data, evaluators, summary_evaluators, experiment_prefix,
#              metadata, max_concurrency)                     -> experiment chalao
#     push_prompt(name, object=prompt) / pull_prompt("name:tag") -> Prompt Hub
#     create_feedback(run_id, key, score, comment, correction) -> user 👍/👎
#     create_presigned_feedback_token(run_id, feedback_key)   -> bina key wala URL
#     flush()                                 -> pending traces ABHI bhej do
#
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
oai = wrap_openai(OpenAI(base_url=GROQ_BASE_URL, api_key=os.getenv("GROQ_API_KEY")), chat_name="ChatGroq")
ls_client = Client()


# client=ls_client: taake neeche ls_client.flush() isi ke traces bheje
@traceable(name="Support Reply", client=ls_client)
def support_reply(question: str) -> str:
    resp = oai.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "Watch store support. Only COD. Reply in 1 line."},
            {"role": "user", "content": question},
        ],
    )
    return resp.choices[0].message.content


def handle_request(question: str) -> dict:
    run_id = uuid.uuid4()
    answer = support_reply(question, langsmith_extra={"run_id": run_id})
    return {"answer": answer, "run_id": str(run_id)}  # run_id client ko wapas


if __name__ == "__main__":
    r1 = handle_request("Kya JazzCash se payment ho sakti hai?")
    r2 = handle_request("Delivery charges?")
    print(r1, "\n", r2)

    # Trace server par pohanchne do, phir feedback (real app mein user der se click karta hai)
    ls_client.flush()

    # 👍 positive
    ls_client.create_feedback(r1["run_id"], key="user_rating", score=1, comment="Helpful")

    # 👎 negative + correction (sahi jawab kya hona chahiye tha — dataset ke liye gold)
    ls_client.create_feedback(
        r2["run_id"],
        key="user_rating",
        score=0,
        comment="Charges nahi bataye",
        correction={"answer": "Rs. 3000 se upar free, warna Rs. 200."},
    )

    # Presigned URL: frontend bina API key ke feedback de sake (e.g. email/WhatsApp link)
    token = ls_client.create_presigned_feedback_token(r1["run_id"], feedback_key="user_rating")
    print("\nPresigned feedback URL:", token.url)

    print("\nUI: project mein 'Feedback' column dekho, ya filter: feedback user_rating = 0")
