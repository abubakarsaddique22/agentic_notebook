from __future__ import annotations

# ---------------------------------------------------------
# DEEPEVAL TIMEOUTS (deepeval import hone se PEHLE set hone chahiye)
# Slow reasoning judge (gpt-oss cloud) + max_concurrent=1 ma baad wale test
# cases semaphore ka intezar karte hain, aur wo intezar bhi time budget
# ma count hota ha. Is liye budget barha diya.
# ---------------------------------------------------------
import os

os.environ.setdefault("DEEPEVAL_PER_TASK_TIMEOUT_SECONDS_OVERRIDE", "3600")     # ek task ka total budget
os.environ.setdefault("DEEPEVAL_PER_ATTEMPT_TIMEOUT_SECONDS_OVERRIDE", "300")   # judge ki ek call ka limit
os.environ.setdefault("DEEPEVAL_TASK_GATHER_BUFFER_SECONDS_OVERRIDE", "120")    # gather/cleanup buffer
# ---------------------------------------------------------
# Ye 3 DEEPEVAL_* environment variables DeepEval khud parhta ha (import ke waqt
# apni settings banate hue), is liye inhe deepeval import se PEHLE set karna zaroori ha.
#   PER_TASK_TIMEOUT      -> ek metric ka ek test case pe poora kaam (saari judge
#                            calls + retries + semaphore ka intezar) kitni der tak
#                            chal sakta ha. Is se zyada = timeout error. (3600s = 1 ghanta)
#   PER_ATTEMPT_TIMEOUT   -> judge LLM ki EK call kitni der tak. Slow reasoning
#                            model ke liye 300s.
#   TASK_GATHER_BUFFER    -> saare async tasks ikathe (gather) karte waqt extra
#                            buffer time, taake cleanup ke dauran kaam kat na jaye.
# os.environ.setdefault -> sirf tab set karo jab pehle se set na ho, yani .env /
# terminal ma aap ne value di ho to wohi chalegi.
# ---------------------------------------------------------

import re
import time
import asyncio
import logging

from dotenv import load_dotenv
from openai import OpenAI, AsyncOpenAI
from pydantic import BaseModel

from deepeval.models import DeepEvalBaseLLM

try:
    import json_repair                     # pip install json-repair
except ImportError:                        # na ho to bhi chalay, bas repair fallback off
    json_repair = None

load_dotenv()   # .env se OLLAMA_* / EVAL_JUDGE_MODEL utha lo (agar hain)

log = logging.getLogger("judge")


# =========================================================
# CONFIG
# =========================================================
JUDGE_MODEL = os.getenv("EVAL_JUDGE_MODEL", "gpt-oss:20b-cloud")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY", "ollama")
OLLAMA_MAX_CONCURRENT = int(os.getenv("OLLAMA_MAX_CONCURRENT", "1"))
OLLAMA_TIMEOUT = float(os.getenv("OLLAMA_TIMEOUT", "300"))
OLLAMA_MAX_RETRIES = int(os.getenv("OLLAMA_MAX_RETRIES", "4"))


def _is_rate_limit(err: Exception) -> bool:
    text = str(err).lower()
    return "429" in text or "too many concurrent" in text or "rate limit" in text


def _wait_seconds(err: Exception, attempt: int) -> float:
    # Rate limit ko asli cooldown chahiye, chota backoff wapas 429 hi khayega.
    return 10 * (attempt + 1) if _is_rate_limit(err) else 2 ** attempt


# =========================================================
# OLLAMA JUDGE
# =========================================================

class OllamaJudge(DeepEvalBaseLLM):
    """DeepEval-compatible judge jo Ollama ke OpenAI-compatible /v1 endpoint se
    baat karta ha (local server ya Ollama Cloud -- same code, sirf URL alag)."""

    def __init__(
        self,
        model: str = JUDGE_MODEL,
        base_url: str = OLLAMA_BASE_URL,
        api_key: str = OLLAMA_API_KEY,
        max_retries: int = OLLAMA_MAX_RETRIES,
        timeout: float = OLLAMA_TIMEOUT,
        max_concurrent: int = OLLAMA_MAX_CONCURRENT,
    ):
        self.model = model
        self.base_url = base_url
        self.max_retries = max_retries
        self.max_concurrent = max_concurrent

        # Ollama API key ignore karta ha, lekin OpenAI client ko chahiye.
        self.client = OpenAI(api_key=api_key, base_url=base_url, timeout=timeout)
        self.async_client = AsyncOpenAI(api_key=api_key, base_url=base_url, timeout=timeout)

        # Semaphore lazily banta ha. Har evaluate() call apna naya event loop
        # chala sakta ha, aur asyncio.Semaphore ek loop se bandh jata ha.
        # Loop badle to naya semaphore -> "bound to a different event loop" error nahi.
        self._semaphore = None
        self._semaphore_loop = None

    # ---------- DeepEval required ----------
    def load_model(self):
        return self.client

    def get_model_name(self):
        return f"ollama/{self.model}"

    # ---------- request ----------
    def _build_kwargs(self, prompt: str, schema, attempt: int = 0):
        kwargs = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            # attempt 0 -> 0.0, phir 0.3, 0.6, 0.9
            # (temperature 0 par retry ka wohi output aata ha, is liye barhate hain)
            "temperature": min(0.3 * attempt, 0.9),
            "max_tokens": 8000,
            "reasoning_effort": "low",
        }

        # DeepEval pydantic schema deta ha (score + reason waghera).
        # Ollama ko bolo exactly wohi JSON shape wapas kare.
        if schema is not None:
            kwargs["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": "deepeval_output",
                    "strict": False,
                    "schema": schema.model_json_schema(),
                },
            }

        return kwargs

    # ---------- response ----------
    @staticmethod
    def _extract(response) -> str:
        choice = response.choices[0]
        content = choice.message.content

        if not content:
            raise ValueError(
                f"Ollama judge returned an empty response (finish_reason={choice.finish_reason})"
            )

        return content

    @staticmethod
    def _parse(content: str, schema):
        if schema is None:
            return content

        # ```json fences hata do (kuch models response_format ke bawajood lagate hain)
        cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", content.strip())

        try:
            return schema.model_validate_json(cleaned)
        except Exception:
            if json_repair is None:
                raise
            # missing ] / } jaisi choti ghaltiyan yahan theek ho jati hain
            data = json_repair.loads(cleaned)
            return schema.model_validate(data)

    def _get_semaphore(self) -> asyncio.Semaphore:
        loop = asyncio.get_running_loop()
        if self._semaphore is None or self._semaphore_loop is not loop:
            self._semaphore = asyncio.Semaphore(self.max_concurrent)
            self._semaphore_loop = loop
        return self._semaphore

    # ---------- DeepEval interface ----------
    def generate(self, prompt: str, schema: BaseModel | None = None):
        last_err = None

        for attempt in range(self.max_retries):
            try:
                response = self.client.chat.completions.create(
                    **self._build_kwargs(prompt, schema, attempt)
                )
                return self._parse(self._extract(response), schema)
            except Exception as e:  # noqa: BLE001 -- har transient error pe retry
                last_err = e
                if attempt < self.max_retries - 1:
                    wait_s = _wait_seconds(e, attempt)
                    log.warning("judge retry %d/%d in %.0fs: %s", attempt + 1, self.max_retries, wait_s, e)
                    time.sleep(wait_s)

        raise ValueError(f"Ollama judge failed after {self.max_retries} retries: {last_err}")

    async def a_generate(self, prompt: str, schema: BaseModel | None = None):
        last_err = None
        semaphore = self._get_semaphore()

        for attempt in range(self.max_retries):
            try:
                # semaphore sirf request ke dauran pakro, sleep ke dauran nahi,
                # taake retry wali call doosri calls ko block na kare
                async with semaphore:
                    response = await self.async_client.chat.completions.create(
                        **self._build_kwargs(prompt, schema, attempt)
                    )
                return self._parse(self._extract(response), schema)
            except Exception as e:  # noqa: BLE001
                last_err = e
                if attempt < self.max_retries - 1:
                    wait_s = _wait_seconds(e, attempt)
                    log.warning("judge retry %d/%d in %.0fs: %s", attempt + 1, self.max_retries, wait_s, e)
                    await asyncio.sleep(wait_s)

        raise ValueError(f"Ollama judge failed after {self.max_retries} retries: {last_err}")


# =========================================================
# SHARED INSTANCE
# =========================================================
_judges: dict[str, OllamaJudge] = {}


def get_judge(model: str | None = None) -> OllamaJudge:
    """Poore run ke liye ek hi judge instance (har model ka ek).
    Har eval file isay call kare, khud OllamaJudge() na banaye, taake
    config change (.env) har metric pe ek jaisa lage."""
    model = model or JUDGE_MODEL
    if model not in _judges:
        _judges[model] = OllamaJudge(model=model)
        print(f"[judge] {model} @ {OLLAMA_BASE_URL} (max_concurrent={OLLAMA_MAX_CONCURRENT})")
    return _judges[model]


# quick smoke test: python judge.py
if __name__ == "__main__":
    class _Check(BaseModel):
        verdict: str
        reason: str

    j = get_judge()
    print("plain :", j.generate("Reply with one word: hello"))
    print("schema:", j.generate('Is 2+2=4? Reply as JSON with keys "verdict" (yes/no) and "reason".', schema=_Check))
