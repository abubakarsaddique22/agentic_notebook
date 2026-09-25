"""
evals/eval_rag_pipeline.py
==========================
End-to-end evaluation of the WHOLE RAG pipeline (retrieve -> rerank -> generate)
using the RAG triad:

    ContextualRelevancy : retriever ne jo context diya, kya woh query se relevant ha?
    Faithfulness        : answer ke claims context se supported hain?
    AnswerRelevancy     : answer query ka jawab deta ha?

Setup (one time):
    pip install json-repair
    ollama signin

Run:
    python -m evals.eval_rag_pipeline
"""

print("[1] eval_rag_pipeline.py started")

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
# IMPORT ORDER MATTERS (Windows):
# src.* (reranker -> torch / sentence-transformers / chroma) MUST be imported
# BEFORE deepeval / openai. Ulta order ma DLL conflict se process bina error
# ke chup-chaap exit ho jata ha.
# ---------------------------------------------------------
from src.rag_pipeline import RagPipeline

print("[2] pipeline imported")

import re
import asyncio

import json_repair
from dotenv import load_dotenv
from openai import OpenAI, AsyncOpenAI
from pydantic import BaseModel

from deepeval import evaluate
from deepeval.evaluate.configs import AsyncConfig
from deepeval.test_case import LLMTestCase
from deepeval.metrics import (
    FaithfulnessMetric,
    AnswerRelevancyMetric,
    ContextualRelevancyMetric,
)
from deepeval.models import DeepEvalBaseLLM

from evals.harness import load_goldens, summarize_by_metric, print_summary

print("[3] deepeval imported")

load_dotenv()

GOLDEN_PATH = "goldens/faithfulness_dataset.json"   # sirf queries reuse ho rahi hain
JUDGE_MODEL = "gpt-oss:20b-cloud"                   # Ollama cloud judge
OLLAMA_BASE_URL = "http://localhost:11434/v1"
THRESHOLD = 0.7
MAX_CONCURRENT = 1                                  # 1 = sab se stable, 2 = tez lekin risky


# =========================================================
# OLLAMA JUDGE (JSON repair + smart retries)
# =========================================================

class OllamaJudge(DeepEvalBaseLLM):

    def __init__(self, model=JUDGE_MODEL, base_url=OLLAMA_BASE_URL, max_retries: int = 4):
        self.model = model
        self.max_retries = max_retries

        # Ollama API key ignore karta ha, lekin OpenAI client ko chahiye.
        self.client = OpenAI(api_key="ollama", base_url=base_url)
        self.async_client = AsyncOpenAI(api_key="ollama", base_url=base_url)

    def load_model(self):
        return self.client

    def get_model_name(self):
        return self.model

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
    def _extract(response):
        choice = response.choices[0]
        content = choice.message.content

        if not content:
            raise ValueError(
                f"Ollama returned an empty response (finish_reason={choice.finish_reason})"
            )

        return content

    @staticmethod
    def _parse(content: str, schema):
        if schema is None:
            return content

        # ```json fences hata do
        cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", content.strip())

        try:
            return schema.model_validate_json(cleaned)
        except Exception:
            # missing ] / } jaisi choti ghaltiyan yahan theek ho jati hain
            data = json_repair.loads(cleaned)
            return schema.model_validate(data)

    # ---------- DeepEval interface ----------
    def generate(self, prompt: str, schema: BaseModel | None = None):
        last_err = None

        for attempt in range(self.max_retries):
            try:
                response = self.client.chat.completions.create(
                    **self._build_kwargs(prompt, schema, attempt)
                )
                return self._parse(self._extract(response), schema)
            except Exception as e:
                last_err = e

        raise ValueError(f"Judge failed after retries: {last_err}")

    async def a_generate(self, prompt: str, schema: BaseModel | None = None):
        last_err = None

        for attempt in range(self.max_retries):
            try:
                response = await self.async_client.chat.completions.create(
                    **self._build_kwargs(prompt, schema, attempt)
                )
                return self._parse(self._extract(response), schema)
            except Exception as e:
                last_err = e
                await asyncio.sleep(2 ** attempt)

        raise ValueError(f"Judge failed after retries: {last_err}")


# =========================================================
# EVAL
# =========================================================

def run(rag):
    # 1. LOAD queries (sirf queries chahiye, context ab pipeline se aata ha)
    goldens = load_goldens(GOLDEN_PATH)
    print(f"Loaded {len(goldens)} queries from {GOLDEN_PATH}")

    # 2. RUN THE PIPELINE per query, LIVE output se test case banao
    test_cases = []
    for g in goldens:
        result = rag.invoke(g["query"])          # retrieve -> rerank -> generate

        test_cases.append(
            LLMTestCase(
                input=g["query"],
                actual_output=result["answer"],       # generator ka answer
                retrieval_context=result["context"],  # retriever ne jo diya
            )
        )

    # 3. JUDGE: sirf ek dafa, loop ke BAHAR
    judge = OllamaJudge(model=JUDGE_MODEL)

    # 4. THE THREE TRIAD METRICS
    metrics = [
        ContextualRelevancyMetric(threshold=THRESHOLD, model=judge, include_reason=True),
        FaithfulnessMetric(threshold=THRESHOLD, model=judge, include_reason=True),
        AnswerRelevancyMetric(threshold=THRESHOLD, model=judge, include_reason=True),
    ]

    # 5. EVALUATE
    result = evaluate(
        test_cases=test_cases,
        metrics=metrics,
        async_config=AsyncConfig(max_concurrent=MAX_CONCURRENT),
    )
    return summarize_by_metric(result)


def run_local():
    """Standalone convenience: pipeline banao, phir run karo."""
    return run(RagPipeline())


if __name__ == "__main__":
    print_summary("rag_pipeline", run_local())