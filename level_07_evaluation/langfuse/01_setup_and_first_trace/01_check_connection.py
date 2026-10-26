"""
Step 1: Setup check.

  - .env load karo (langfuse import se PEHLE)
  - zaroori env vars check karo
  - auth_check() se Langfuse server se connect karo

Note: auth_check() sirf setup/debugging ke liye hai — production code mein mat lagana (latency barhata hai).
"""
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

from langfuse import get_client  # noqa: E402


def check_python() -> bool:
    ok = sys.version_info >= (3, 11)
    print(f"[{'OK' if ok else 'FAIL'}]      Python {sys.version.split()[0]} (3.11+ chahiye)")
    return ok


def check_env() -> bool:
    ok = True
    for key in ["LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY", "OPENAI_API_KEY"]:
        value = os.getenv(key)
        if not value or "xxxx" in value:
            print(f"[MISSING] {key}  -> .env mein set karo")
            ok = False
        else:
            print(f"[OK]      {key} = {value[:10]}...")
    print(f"[INFO]    LANGFUSE_BASE_URL = {os.getenv('LANGFUSE_BASE_URL', 'https://cloud.langfuse.com')}")
    print(f"[INFO]    LANGFUSE_TRACING_ENVIRONMENT = {os.getenv('LANGFUSE_TRACING_ENVIRONMENT', 'default')}")
    return ok


if __name__ == "__main__":
    if check_python() and check_env():
        langfuse = get_client()  # singleton — poori app mein yahi milega
        if langfuse.auth_check():
            print("\n[OK] Langfuse se connect ho gaya. Ab 02_first_trace.py chalao.")
        else:
            print("\n[FAIL] Auth fail. Keys aur LANGFUSE_BASE_URL (EU/US region) check karo.")
    else:
        print("\nPehle upar wale masle theek karo.")
