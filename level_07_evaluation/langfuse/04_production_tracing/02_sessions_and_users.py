"""
Sessions + Users: multi-turn chatbot ki poori conversation, aur har customer ka hisaab.

  session_id -> Sessions tab mein ek conversation (har message ek trace)
  user_id    -> Users tab mein us customer ki sab traces, tokens, cost

WhatsApp/website chatbots ke liye must-have.
"""
import os
import uuid
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from langfuse import get_client, observe, propagate_attributes  # noqa: E402
from langfuse.openai import OpenAI  # noqa: E402

MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
langfuse = get_client()
client = OpenAI()

# Real app mein Redis / DB
CONVERSATIONS: dict[str, list[dict]] = {}


@observe(name="chat-turn")
def chat_turn(session_id: str, user_id: str, user_message: str) -> str:
    with propagate_attributes(session_id=session_id, user_id=user_id):
        history = CONVERSATIONS.setdefault(
            session_id, [{"role": "system", "content": "You are a short, friendly watch store assistant."}]
        )
        history.append({"role": "user", "content": user_message})

        resp = client.chat.completions.create(model=MODEL, messages=history, name="chat-reply")
        reply = resp.choices[0].message.content
        history.append({"role": "assistant", "content": reply})
        return reply


if __name__ == "__main__":
    session = f"whatsapp-{uuid.uuid4().hex[:8]}"
    # Real user ID / phone number ki jagah hash ya internal customer ID use karo
    user = "customer-1042"
    for msg in ["Salam, mujhe gift ke liye watch chahiye", "Budget 5000 hai", "Black color mein?"]:
        print("User:", msg)
        print("Bot :", chat_turn(session, user, msg), "\n")

    langfuse.flush()
    print(f"UI: Sessions tab -> '{session}' kholo. Users tab -> '{user}'.")
