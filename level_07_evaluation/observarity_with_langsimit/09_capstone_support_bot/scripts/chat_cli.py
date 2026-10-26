"""
Terminal chat — bot ko test karo aur har jawab par feedback do.

Chalao (09_capstone_support_bot folder se):
    python -m scripts.chat_cli

Commands:  'exit' -> band,  'new' -> nayi conversation (naya thread)
"""
import uuid

from app.settings import APP_ENV, ls_client

from app.bot import chat, record_feedback


def new_thread() -> str:
    return f"cli-{uuid.uuid4().hex[:8]}"


if __name__ == "__main__":
    thread_id = new_thread()
    print(f"Watch Support Bot ({APP_ENV}) | thread={thread_id}")
    print("Type 'exit' to quit, 'new' for new conversation.\n")

    try:
        while True:
            q = input("You: ").strip()
            if not q:
                continue
            if q.lower() == "exit":
                break
            if q.lower() == "new":
                thread_id = new_thread()
                print(f"-- new thread: {thread_id} --\n")
                continue

            result = chat(q, thread_id=thread_id, user_id="cli-user")
            print(f"Bot: {result.answer}")
            print(f"     (sources: {result.sources or 'none'})")

            fb = input("     Feedback? [y = good / n = bad / Enter = skip]: ").strip().lower()
            if fb in ("y", "n"):
                comment = input("     Comment (optional): ").strip() or None
                record_feedback(result.run_id, 1 if fb == "y" else 0, comment)
                print("     feedback saved.")
            print()
    finally:
        ls_client.flush()
        print("Traces flushed. LangSmith UI mein project 'watch-support-bot-dev' dekho.")
