"""
Distributed tracing: request Service A (gateway) se Service B (AI service) mein HTTP se jati hai.
Dono services ke runs EK hi trace mein chahiye.

Tareeqa:
  Service A: run_tree.to_headers() -> HTTP headers mein bhejo
  Service B: tracing_context(parent=request.headers) -> wahi trace continue

Yahan dono services ek file mein hain (FastAPI TestClient se), real life mein alag servers.
"""
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

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
from fastapi import FastAPI, Request  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
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
from langsmith.run_helpers import get_current_run_tree  # noqa: E402
# ---------------------------------------------------------
# get_current_run_tree  (function) -- abhi chal raha run (RunTree) wapas deta ha
#   @traceable function ke andar call karo; bahar ho to None.
#   RunTree ke kaam ke methods:
#     run.add_metadata({...}) -> runtime pe metadata (jo pehle pata nahi tha)
#     run.add_tags([...])     -> runtime pe tags
#     run.to_headers()        -> HTTP headers -- doosri service isi trace ko aage chalaye
#     run.end(outputs=...)    -> run khatam + output set
#     run.id / run.trace_id   -> IDs
# ---------------------------------------------------------

# ================= Service B: AI service =================
ai_service = FastAPI()


@traceable(name="AI Service: Generate Reply")
def generate_reply(text: str) -> str:
    return f"AI reply for: {text}"


@ai_service.post("/reply")
async def reply_endpoint(request: Request):
    body = await request.json()
    # Headers se parent trace pick karo -> yeh run Service A ke trace ka child banega
    with ls.tracing_context(parent=request.headers):
        answer = generate_reply(body["text"])
    return {"answer": answer}


ai_http = TestClient(ai_service)  # real life mein: httpx.post("http://ai-service/reply", ...)


# ================= Service A: Gateway =================
@traceable(name="Gateway: Incoming WhatsApp Message")
def gateway(text: str) -> str:
    run = get_current_run_tree()
    headers = run.to_headers() if run else {}
    resp = ai_http.post("/reply", json={"text": text}, headers=headers)
    return resp.json()["answer"]


if __name__ == "__main__":
    print(gateway("Order kab aayega?"))
    print("UI: ek hi trace mein Gateway -> AI Service dono runs nested dikhne chahiye.")
