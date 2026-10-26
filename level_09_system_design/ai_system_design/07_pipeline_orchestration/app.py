"""
Module 7 · Orchestration patterns in FastAPI
============================================

Teen execution patterns, ek app mein:

  1. SYNC        POST /chat               request -> pipeline -> response (user wait karta hai, ~1-3s)
  2. ACK + ASYNC POST /webhook/whatsapp   foran 200 OK, processing BACKGROUND mein
                                          (WhatsApp/Meta webhooks ko jaldi 200 chahiye, warna retry
                                          karte hain -> duplicate messages. Is liye IDEMPOTENCY.)
  3. JOB         POST /reports  -> 202 + job_id;  GET /jobs/{id} -> status/result
                                          (lamba kaam: 30s-10min. User ko wait mat karwao)

Production mein (Level 10):
  - Background kaam -> REAL QUEUE (Redis + arq/RQ/Celery, ya AWS SQS) + alag worker process
  - Job store + processed-message IDs -> Redis / Postgres (yahan in-memory dict hai)

Chalane ka tareeqa (PowerShell, root folder, venv active):
    pip install fastapi uvicorn httpx
    uvicorn app:app --app-dir 07_pipeline_orchestration --reload
    -> browser: http://127.0.0.1:8000/docs   (har endpoint wahan se try karo)

    Ya bina server ke saare scenarios:
    python 07_pipeline_orchestration\\try_app.py
"""

from __future__ import annotations

import time
import uuid
from typing import Literal

from fastapi import BackgroundTasks, FastAPI, HTTPException
from pydantic import BaseModel

try:
    from components import (FakeShopifyOrders, KeywordRetriever, RuleIntentClassifier,
                            SupportPipeline, default_llm)
except ImportError:  # jab root se `python -m` ya test ke through import ho
    from .components import (FakeShopifyOrders, KeywordRetriever,  # type: ignore
                             RuleIntentClassifier, SupportPipeline, default_llm)

from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Support bot: orchestration patterns")

# Composition root: yahan decide hota hai kaun si implementation lagegi.
pipeline = SupportPipeline(RuleIntentClassifier(), KeywordRetriever(), default_llm(),
                           FakeShopifyOrders())

# In-memory stores (production: Redis/Postgres)
PROCESSED_MESSAGE_IDS: set[str] = set()
OUTBOX: list[dict] = []                    # "bheje gaye" WhatsApp messages (demo)
JOBS: dict[str, dict] = {}


# ==========================================================================
# 1) SYNC
# ==========================================================================


class ChatIn(BaseModel):
    text: str


@app.post("/chat")
def chat(body: ChatIn) -> dict:
    t = time.perf_counter()
    r = pipeline.handle(body.text)
    return {"reply": r.reply, "intent": r.intent, "route": r.route, "steps": r.steps,
            "total_ms": round((time.perf_counter() - t) * 1000, 1)}


# ==========================================================================
# 2) ACK fast + process in background (WhatsApp webhook pattern) + idempotency
# ==========================================================================


class WhatsAppIn(BaseModel):
    message_id: str          # Meta har message ki unique id deta hai (wamid...)
    from_number: str
    text: str


def process_whatsapp(msg: WhatsAppIn) -> None:
    r = pipeline.handle(msg.text)
    OUTBOX.append({"to": msg.from_number, "reply": r.reply, "route": r.route,
                   "in_reply_to": msg.message_id})   # production: Meta Graph API call


@app.post("/webhook/whatsapp")
def whatsapp_webhook(msg: WhatsAppIn, bg: BackgroundTasks) -> dict:
    # Idempotency: Meta same message dobara bhej sakta hai (retries). Dobara process mat karo.
    if msg.message_id in PROCESSED_MESSAGE_IDS:
        return {"status": "duplicate_ignored"}
    PROCESSED_MESSAGE_IDS.add(msg.message_id)
    bg.add_task(process_whatsapp, msg)      # production: queue.enqueue(...)
    return {"status": "accepted"}           # ~ms mein 200 OK


@app.get("/outbox")
def outbox() -> list[dict]:
    return OUTBOX


# ==========================================================================
# 3) Long-running JOB (async): 202 Accepted + polling
# ==========================================================================


class ReportIn(BaseModel):
    kind: Literal["weekly_faq_summary", "unanswered_questions"]


def run_report(job_id: str, kind: str) -> None:
    JOBS[job_id]["status"] = "running"
    try:
        time.sleep(0.3)                      # asal mein: logs padhna, 100s LLM calls (Batch API)
        JOBS[job_id].update(status="done", result={
            "kind": kind, "top_questions": ["return policy", "delivery time", "COD"],
            "unanswered": 7})
    except Exception as e:  # noqa: BLE001
        JOBS[job_id].update(status="failed", error=str(e))


@app.post("/reports", status_code=202)
def create_report(body: ReportIn, bg: BackgroundTasks) -> dict:
    job_id = uuid.uuid4().hex[:8]
    JOBS[job_id] = {"status": "queued", "kind": body.kind, "created": time.time()}
    bg.add_task(run_report, job_id, body.kind)
    return {"job_id": job_id, "status": "queued", "poll": f"/jobs/{job_id}"}


@app.get("/jobs/{job_id}")
def get_job(job_id: str) -> dict:
    if job_id not in JOBS:
        raise HTTPException(404, "job not found")
    return JOBS[job_id]


@app.get("/health")
def health() -> dict:
    return {"ok": True, "llm": type(pipeline.llm).__name__}
