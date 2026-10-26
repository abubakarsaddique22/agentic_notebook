"""
Central config — app ki har cheez yahan se settings leti hai.

IMPORTANT: Yeh module baqi sab se PEHLE import hota hai, kyunke LangSmith env vars
(project name wagera) langsmith import hone se pehle set hone chahiye.
"""
import os
import re
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]  # langsimit/
PROJECT_DIR = Path(__file__).resolve().parents[1]  # 09_capstone_support_bot/
load_dotenv(ROOT / ".env")

# ---------------- App identity ----------------
APP_NAME = "watch-support-bot"
APP_ENV = os.getenv("APP_ENV", "dev")  # dev | staging | prod
APP_VERSION = "1.0.0"

# Har environment ka alag LangSmith project (folder 04 ka concept)
os.environ["LANGSMITH_PROJECT"] = f"{APP_NAME}-{APP_ENV}"

# Prod mein sab trace karna mehnga ho sakta hai (folder 04: sampling)
if APP_ENV == "prod":
    os.environ.setdefault("LANGSMITH_TRACING_SAMPLING_RATE", "0.25")

# ---------------- LLM ----------------
# Groq OpenAI-compatible API: OpenAI SDK + ye URL + GROQ_API_KEY
GROQ_BASE_URL = "https://api.groq.com/openai/v1"
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")               # bot ka model
JUDGE_MODEL = os.getenv("GROQ_JUDGE_MODEL", "openai/gpt-oss-120b")     # evals ka judge
STORE_NAME = "Watch Store"

# ---------------- Prompt Hub (folder 07) ----------------
PROMPT_NAME = "watch-support-bot-prompt"
PROMPT_ID = os.getenv("BOT_PROMPT_ID", PROMPT_NAME)  # prod mein: "watch-support-bot-prompt:prod"

# ---------------- Data ----------------
FAQ_PATH = PROJECT_DIR / "data" / "faq.json"
EVAL_DATASET = "watch-support-bot-golden"
MAX_HISTORY_MESSAGES = 6

# ---------------- PII masking (folder 04) ----------------
_PHONE_RE = re.compile(r"(\+92|0)3\d{2}[-\s]?\d{7}")
_EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")


def _mask(value):
    if isinstance(value, str):
        return _EMAIL_RE.sub("<EMAIL>", _PHONE_RE.sub("<PHONE>", value))
    if isinstance(value, dict):
        return {k: _mask(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_mask(v) for v in value]
    return value


def mask_pii(data: dict) -> dict:
    return _mask(dict(data))


# Langsmith import yahan (env set hone ke BAAD)
from langsmith import Client  # noqa: E402
# ---------------------------------------------------------
# Client  (class) -- LangSmith API se baat karne wala object
#   Client() .env se LANGSMITH_API_KEY / LANGSMITH_ENDPOINT khud uthata ha.
#   Constructor options: api_key, api_url, hide_inputs / hide_outputs (masking
#   function ya True), anonymizer, auto_batch_tracing (default True).
#   Is project ma use hone wale methods:
#     list_projects()                         -> projects ki list
#     list_runs(project_name, is_root, error, start_time, filter, limit) -> traces query
#     has_dataset / read_dataset / create_dataset(dataset_name, description)
#     create_examples(dataset_id, examples=[{inputs, outputs, metadata, split}])
#     list_examples(dataset_name, splits=[...], as_of="prod")  -> examples parho
#     update_dataset_tag(dataset_name, as_of=datetime, tag)   -> version ko tag
#     evaluate(target, data, evaluators, summary_evaluators, experiment_prefix,
#              metadata, max_concurrency)                     -> experiment chalao
#     push_prompt(name, object=prompt) / pull_prompt("name:tag") -> Prompt Hub
#     create_feedback(run_id, key, score, comment, correction) -> user 👍/👎
#     create_presigned_feedback_token(run_id, feedback_key)   -> bina key wala URL
#     flush()                                 -> pending traces ABHI bhej do
# ---------------------------------------------------------

# Poori app yahi client use karegi -> masking har trace par lagegi
ls_client = Client(hide_inputs=mask_pii, hide_outputs=mask_pii)

COMMON_METADATA = {"app_version": APP_VERSION, "env": APP_ENV}
