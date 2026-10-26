"""
Central config — app ki har cheez yahan se settings leti hai.

IMPORTANT: Yeh module baqi sab se PEHLE import hota hai. Yahan config wala Langfuse client
(environment, release, masking, sampling) banta hai. Langfuse singleton hai — baad mein
@observe, langfuse.openai aur get_client() sab isi client ko use karte hain.
"""
import os
import re
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]  # langfuse/
PROJECT_DIR = Path(__file__).resolve().parents[1]  # 10_capstone_support_bot/
load_dotenv(ROOT / ".env")

from langfuse import Langfuse  # noqa: E402

# ---------------- App identity ----------------
APP_NAME = "watch-support-bot"
APP_ENV = os.getenv("APP_ENV", "development")  # development | staging | production
APP_VERSION = "1.0.0"

# ---------------- LLM ----------------
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
STORE_NAME = "Watch Store"

# ---------------- Prompt Management (folder 07) ----------------
PROMPT_NAME = "watch-support-bot"
PROMPT_LABEL = os.getenv("BOT_PROMPT_LABEL", "production")  # staging test karne ke liye: staging

# ---------------- Data ----------------
FAQ_PATH = PROJECT_DIR / "data" / "faq.json"
EVAL_DATASET = "capstone/watch-support-golden"  # slash = folder in Langfuse UI
MAX_HISTORY_MESSAGES = 6

# ---------------- PII masking (folder 04) ----------------
_PHONE_RE = re.compile(r"(\+92|0)3\d{2}[-\s]?\d{7}")
_EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
_CNIC_RE = re.compile(r"\d{5}-\d{7}-\d")


def mask_pii(*, data: Any, **kwargs: Any) -> Any:
    if isinstance(data, str):
        return _EMAIL_RE.sub("<EMAIL>", _CNIC_RE.sub("<CNIC>", _PHONE_RE.sub("<PHONE>", data)))
    if isinstance(data, dict):
        return {k: mask_pii(data=v) for k, v in data.items()}
    if isinstance(data, (list, tuple)):  # tuple zaroori: @observe positional args tuple mein bhejta hai
        return [mask_pii(data=v) for v in data]
    return data


# ---------------- Langfuse client (singleton, sabse pehle) ----------------
# Production mein sirf 25% traces (folder 04: sampling). Experiments/evals hamesha
# development mein chalao — sampling < 1 par experiment results adhoore hote hain.
SAMPLE_RATE = 0.25 if APP_ENV == "production" else 1.0

langfuse = Langfuse(
    environment=APP_ENV,
    release=APP_VERSION,
    mask=mask_pii,
    sample_rate=SAMPLE_RATE,
)
