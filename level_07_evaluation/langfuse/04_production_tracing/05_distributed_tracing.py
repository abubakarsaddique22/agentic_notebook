"""
Distributed tracing: request Service A (gateway) se Service B (AI service) mein HTTP se jati hai.
Dono services ki observations EK hi trace mein chahiye.

Tareeqa:
  Service A: get_current_trace_id() + get_current_observation_id() -> HTTP headers mein bhejo
  Service B: start_as_current_observation(..., trace_context={"trace_id", "parent_span_id"})

Yahan dono services ek file mein hain (FastAPI TestClient), real life mein alag servers.
"""
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from fastapi import FastAPI, Request  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from langfuse import get_client, observe  # noqa: E402

langfuse = get_client()

# ================= Service B: AI service =================
ai_service = FastAPI()


@observe(name="ai-service-generate-reply")
def generate_reply(text: str) -> str:
    return f"AI reply for: {text}"


@ai_service.post("/reply")
async def reply_endpoint(request: Request):
    body = await request.json()
    trace_id = request.headers.get("x-langfuse-trace-id")
    parent_id = request.headers.get("x-langfuse-parent-id")

    if trace_id and parent_id:
        # Upstream trace join karo -> yeh Service A ke trace ka child banega
        with langfuse.start_as_current_observation(
            as_type="span",
            name="ai-service-request",
            trace_context={"trace_id": trace_id, "parent_span_id": parent_id},
        ):
            answer = generate_reply(body["text"])
    else:
        answer = generate_reply(body["text"])  # headers nahi -> naya trace
    return {"answer": answer}


ai_http = TestClient(ai_service)  # real life mein: httpx.post("http://ai-service/reply", ...)


# ================= Service A: Gateway =================
@observe(name="gateway-incoming-whatsapp-message")
def gateway(text: str) -> str:
    headers = {
        "x-langfuse-trace-id": langfuse.get_current_trace_id() or "",
        "x-langfuse-parent-id": langfuse.get_current_observation_id() or "",
    }
    resp = ai_http.post("/reply", json={"text": text}, headers=headers)
    return resp.json()["answer"]


if __name__ == "__main__":
    print(gateway("Order kab aayega?"))
    langfuse.flush()
    print("UI: ek hi trace mein gateway -> ai-service-request -> generate-reply nested hone chahiye.")
