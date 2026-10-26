"""
Terminal chat — bot test karo aur har jawab par feedback do.

Chalao (10_capstone_support_bot folder se):
    python -m scripts.chat_cli

Commands:  'exit' -> band,  'new' -> nayi conversation (naya session)
"""
import uuid

from app.settings import APP_ENV, langfuse

from app.bot import chat, record_feedback


def new_session() -> str:
    return f"cli-{uuid.uuid4().hex[:8]}"


if __name__ == "__main__":
    session_id = new_session()
    print(f"Watch Support Bot ({APP_ENV}) | session={session_id}")
    print("Type 'exit' to quit, 'new' for new conversation.\n")

    try:
        while True:
            q = input("You: ").strip()
            if not q:
                continue
            if q.lower() == "exit":
                break
            if q.lower() == "new":
                session_id = new_session()
                print(f"-- new session: {session_id} --\n")
                continue

            result = chat(q, session_id=session_id, user_id="cli-user")
            print(f"Bot: {result.answer}")
            print(f"     (sources: {result.sources or 'none'})")

            fb = input("     Feedback? [y = good / n = bad / Enter = skip]: ").strip().lower()
            if fb in ("y", "n") and result.trace_id:
                comment = input("     Comment (optional): ").strip() or None
                record_feedback(result.trace_id, 1 if fb == "y" else 0, comment)
                print("     feedback saved.")
            print()
    finally:
        langfuse.flush()
        print(f"Data flushed. Langfuse UI -> Sessions -> '{session_id}'.")
