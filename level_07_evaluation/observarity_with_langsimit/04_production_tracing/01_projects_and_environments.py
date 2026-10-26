"""
Har environment ka alag project — industry ka standard pattern.

APP_ENV=dev  -> traces "support-bot-dev" mein
APP_ENV=prod -> traces "support-bot-prod" mein

Do tareeqe:
  A) Startup par LANGSMITH_PROJECT env var set karna (sabse simple, poori app par lagta hai)
  B) tracing_context(project_name=...) se kisi specific block ko alag project mein bhejna
"""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

# ---- A) App startup par project decide karo (langsmith import se pehle) ----
APP_NAME = "support-bot"
APP_ENV = os.getenv("APP_ENV", "dev")
APP_VERSION = "1.4.0"
os.environ["LANGSMITH_PROJECT"] = f"{APP_NAME}-{APP_ENV}"

import langsmith as ls  # noqa: E402
# ---------------------------------------------------------
# import langsmith as ls  -- poora package (yahan ls.trace / ls.tracing_context ke liye)
#   ls.trace(name, run_type, inputs, tags, metadata, project_name, parent)
#       -> `with` block ko ek run banata ha (decorator ke bina). Andar run.end(outputs=...)
#   ls.tracing_context(project_name, tags, metadata, parent, enabled, client)
#       -> `with` block ke andar ke SAARE traces pe settings lagao:
#          alag project, extra metadata, parent=headers (distributed tracing),
#          ya enabled=False (tracing band).
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

# Har trace par common metadata — taake baad mein version-wise compare kar sako
COMMON_METADATA = {"app_version": APP_VERSION, "env": APP_ENV}


@traceable(name="Handle Request", metadata=COMMON_METADATA)
def handle_request(text: str) -> str:
    return f"echo: {text}"


if __name__ == "__main__":
    handle_request("hello")
    print(f"Trace gaya project: {os.environ['LANGSMITH_PROJECT']}")

    # ---- B) Sirf yeh block alag project mein (e.g. background jobs / experiments) ----
    with ls.tracing_context(project_name=f"{APP_NAME}-{APP_ENV}-jobs"):
        handle_request("nightly job")
    print(f"Aur yeh gaya: {APP_NAME}-{APP_ENV}-jobs")
