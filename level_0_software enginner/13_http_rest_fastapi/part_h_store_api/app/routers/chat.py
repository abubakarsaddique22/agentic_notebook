import json
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.deps import get_llm, verify_api_key
from app.schemas import ChatRequest, ChatResponse
from app.services import orders as order_service
from app.services.llm import FakeLLM

router = APIRouter(prefix="/chat", tags=["chat"], dependencies=[Depends(verify_api_key)])
LLM = Annotated[FakeLLM, Depends(get_llm)]


@router.post("", response_model=ChatResponse)
async def chat(body: ChatRequest, llm: LLM):
    # Order ka sawal ho to seedha lookup: LLM ka paisa aur waqt bacha
    order_id = order_service.find_order_id(body.message)
    if "order" in body.message.lower() and order_id:
        order = order_service.get_order(order_id)
        if order:
            return {"reply": f"Order {order_id}: {order['status']} ({order['courier'] or 'courier pending'})",
                    "source": "order_lookup"}
        return {"reply": f"Order {order_id} nahi mila, number check karein.", "source": "order_lookup"}
    reply = await llm.complete(body.message, [m.model_dump() for m in body.history])
    return {"reply": reply, "source": "llm"}


@router.post("/stream")
async def chat_stream(body: ChatRequest, llm: LLM):
    async def events():
        async for token in llm.stream(body.message):
            yield f"data: {json.dumps({'token': token})}\n\n"
        yield "data: [DONE]\n\n"
    return StreamingResponse(events(), media_type="text/event-stream")
