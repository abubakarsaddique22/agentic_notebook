"""
FastAPI server — production jaisa entry point.

Chalao (09_capstone_support_bot folder se):
    uvicorn app.api:app --reload

Docs: http://127.0.0.1:8000/docs
"""
from contextlib import asynccontextmanager

from app.settings import APP_ENV, APP_VERSION, ls_client

from app.bot import chat, record_feedback
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    ls_client.flush()  # server band hone se pehle pending traces bhej do


app = FastAPI(title="Watch Support Bot", version=APP_VERSION, lifespan=lifespan)


class ChatRequest(BaseModel):
    question: str = Field(min_length=1)
    thread_id: str
    user_id: str


class ChatResponse(BaseModel):
    answer: str
    run_id: str
    sources: list[str]


class FeedbackRequest(BaseModel):
    run_id: str
    score: int = Field(ge=0, le=1)  # 1 = 👍, 0 = 👎
    comment: str | None = None


@app.get("/health")
def health():
    return {"status": "ok", "env": APP_ENV, "version": APP_VERSION}


@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(req: ChatRequest):
    result = chat(req.question, thread_id=req.thread_id, user_id=req.user_id)
    return ChatResponse(answer=result.answer, run_id=result.run_id, sources=result.sources)


@app.post("/feedback")
def feedback_endpoint(req: FeedbackRequest):
    try:
        record_feedback(req.run_id, req.score, req.comment)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"status": "recorded"}
