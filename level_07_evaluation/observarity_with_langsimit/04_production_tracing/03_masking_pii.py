"""
PII masking — sensitive data LangSmith tak jane se PEHLE chhupao.

Options:
  1. Env var: LANGSMITH_HIDE_INPUTS=true / LANGSMITH_HIDE_OUTPUTS=true  (sab kuch chhupa deta hai)
  2. Client(hide_inputs=fn, hide_outputs=fn)  -> selective masking (industry mein yahi use hota hai)

Masking sirf TRACE ki copy par lagti hai — tumhara function asal data hi dekhta hai.
"""
import re
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

PHONE_RE = re.compile(r"(\+92|0)3\d{2}[-\s]?\d{7}")
EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
SENSITIVE_KEYS = {"password", "card_number", "cnic", "address"}


def mask_value(value):
    if isinstance(value, str):
        value = PHONE_RE.sub("<PHONE>", value)
        return EMAIL_RE.sub("<EMAIL>", value)
    if isinstance(value, dict):
        return {k: ("<REDACTED>" if k in SENSITIVE_KEYS else mask_value(v)) for k, v in value.items()}
    if isinstance(value, list):
        return [mask_value(v) for v in value]
    return value


def mask(data: dict) -> dict:
    return mask_value(dict(data))


# Masking wala client — isko traceable ko pass karo
masked_client = Client(hide_inputs=mask, hide_outputs=mask)


@traceable(name="Place Order", client=masked_client)
def place_order(customer: dict, note: str) -> dict:
    # Function ke andar asal data available hai
    return {"status": "confirmed", "sms_sent_to": customer["phone"], "note": note}


if __name__ == "__main__":
    place_order(
        customer={
            "name": "Ali",
            "phone": "03001234567",
            "address": "House 12, DHA Lahore",
            "cnic": "35202-1234567-1",
        },
        note="Call me on 0321-7654321 or ali@example.com",
    )
    masked_client.flush()  # script khatam hone se pehle traces bhej do
    print("UI mein trace kholo: phone/email/address/cnic sab masked hone chahiye.")

    # NOTE: wrap_openai ke saath masking:
    #   client = wrap_openai(OpenAI(base_url=GROQ_BASE_URL, api_key=...), tracing_extra={"client": masked_client})
