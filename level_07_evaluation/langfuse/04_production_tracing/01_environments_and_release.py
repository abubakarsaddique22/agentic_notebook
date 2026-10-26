"""
Environments + Release.

environment: "development" / "staging" / "production"  (lowercase, numbers, - _ ; max 40 chars)
release:     app ka version (e.g. git tag / "1.4.0") — dashboards mein version-wise compare

Do tareeqe:
  A) Env vars (recommended — code mein kuch nahi likhna):
       LANGFUSE_TRACING_ENVIRONMENT=production
       LANGFUSE_RELEASE=1.4.0
  B) Constructor:  Langfuse(environment="production", release="1.4.0")
     (constructor value env var par jeet'ti hai)
"""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from langfuse import Langfuse, get_client, observe  # noqa: E402

APP_ENV = os.getenv("APP_ENV", "development")
APP_VERSION = "1.4.0"

# App startup par SABSE PEHLE config wala client banao.
# Baad mein @observe / get_client() isi singleton ko use karenge.
Langfuse(environment=APP_ENV, release=APP_VERSION)
langfuse = get_client()


@observe(name="handle-request")
def handle_request(text: str) -> str:
    return f"echo: {text}"


if __name__ == "__main__":
    handle_request("hello")
    langfuse.flush()
    print(f"Trace bheja: environment={APP_ENV}, release={APP_VERSION}")
    print("UI: top par environment dropdown se filter karo. .env mein APP_ENV=production karke dobara chalao.")
