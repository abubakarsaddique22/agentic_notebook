"""
evals/eval_application.py
=========================
Application-level quality eval of the WHOLE RAG pipeline using GEval:

    Correctness  : reference-based, sirf TRUTH judge karta ha
    Completeness : reference-based, sirf COVERAGE judge karta ha
    Style        : reference-free, sirf TONE judge karta ha

Setup (one time):
    pip install json-repair
    ollama signin

Run:
    python -m evals.eval_application
"""

print("[1] eval_application.py started")

# ---------------------------------------------------------
# DEEPEVAL TIMEOUTS (deepeval import hone se PEHLE set hone chahiye)
# Slow reasoning judge (gpt-oss cloud) ke liye budget barha diya.
# ---------------------------------------------------------
import os

os.environ.setdefault("DEEPEVAL_PER_TASK_TIMEOUT_SECONDS_OVERRIDE", "3600")
os.environ.setdefault("DEEPEVAL_PER_ATTEMPT_TIMEOUT_SECONDS_OVERRIDE", "300")
os.environ.setdefault("DEEPEVAL_TASK_GATHER_BUFFER_SECONDS_OVERRIDE", "120")

# ---------------------------------------------------------
# IMPORT ORDER MATTERS (Windows):
# src.* (reranker -> torch / chroma) deepeval / openai se PEHLE import karo,
# warna DLL conflict se process bina error ke chup-chaap exit ho sakta ha.
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
from deepeval.test_case import LLMTestCase, LLMTestCaseParams
from deepeval.metrics import GEval
from deepeval.metrics.g_eval import Rubric
from deepeval.models import DeepEvalBaseLLM

from evals.harness import load_goldens, summarize_by_metric, print_summary

print("[3] deepeval imported")

load_dotenv()

GOLDEN_PATH = "goldens/correctness_goldens.json"
JUDGE_MODEL = "gpt-oss:20b-cloud"            # Ollama cloud judge
OLLAMA_BASE_URL = "http://localhost:11434/v1"
THRESHOLD = 0.7
MAX_CONCURRENT = 1                            # 1 = sab se stable, 2 = tez lekin risky


# =========================================================
# OLLAMA JUDGE (JSON repair + smart retries)
# =========================================================

class OllamaJudge(DeepEvalBaseLLM):

    def __init__(self, model=JUDGE_MODEL, base_url=OLLAMA_BASE_URL, max_retries: int = 4):
        self.model = model
        self.max_retries = max_retries

        # Ollama API key ignore karta ha, lekin OpenAI client ko chahiye.
        self.client = OpenAI(api_key="ollama", base_url=base_url, timeout=300)
        self.async_client = AsyncOpenAI(api_key="ollama", base_url=base_url, timeout=300)

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
    # 1. LOAD queries + ideal answers
    goldens = load_goldens(GOLDEN_PATH)
    print(f"Loaded {len(goldens)} golden test cases from {GOLDEN_PATH}")

    # 2. RUN THE PIPELINE per query, LIVE output se test case banao
    test_cases = []
    for g in goldens:
        result = rag.invoke(g["question"])          # retrieve -> rerank -> generate

        test_cases.append(
            LLMTestCase(
                input=g["question"],
                actual_output=result["answer"],
                expected_output=g["ideal_answer"],
            )
        )

    # 3. JUDGE: sirf ek dafa, loop ke BAHAR
    judge = OllamaJudge(model=JUDGE_MODEL)

    # 4. THREE APPLICATION-LEVEL QUALITY METRICS

    # 4a. CORRECTNESS --- reference-based, judges TRUTH (not coverage or length)
    correctness = GEval(
        name="Correctness",
        evaluation_steps=[ # jaha pa hum saii tara define kar raha hai tu ab cot skip ho jaa gaa agr hight level hotaa tu phir cot deepeval kuhd step karta
            "Compare only the factual claims in the actual output against the expected output.",
            "A claim is wrong only if it CONTRADICTS the expected output or is factually false. Judge truth, not completeness.",
            "A factually accurate answer must score at least 0.9 even if it is shorter or covers fewer points than the expected output.",
            "Do NOT deduct for brevity, missing elaboration, or omitted points --- omissions are not errors here.",
            "Additional correct information must NEVER lower the score.",
        ],
        rubric=[ # rubric define karta ha ki kis range ma kya outcome expect hota ha
            Rubric(score_range=(9, 10), expected_outcome="All stated claims are factually correct and consistent. No contradictions. Brevity is fine."),
            Rubric(score_range=(5, 8),  expected_outcome="Mostly correct but one minor inaccuracy."),
            Rubric(score_range=(0, 4),  expected_outcome="Contains a clear factual error or a claim that contradicts the expected output."),
        ],
        evaluation_params=[LLMTestCaseParams.INPUT, LLMTestCaseParams.ACTUAL_OUTPUT, LLMTestCaseParams.EXPECTED_OUTPUT],
        threshold=THRESHOLD,
        model=judge,
        strict_mode=False,
    )

    # 4b. COMPLETENESS --- reference-based, judges COVERAGE (not correctness)
    completeness = GEval(
        name="Completeness",
        evaluation_steps=[ 
            "Identify the key points contained in the expected output.",
            "Check how many of those key points are addressed in the actual output.",
            "Penalize the actual output for each key point from the expected output that it omits or only partially covers.",
            "Judge coverage only. Do NOT lower the score because a covered point is stated incorrectly --- factual correctness is judged separately.",
            "Do NOT penalize the actual output for adding extra information beyond the expected output.",
        ],
        rubric=[
            Rubric(score_range=(9, 10), expected_outcome="Addresses essentially all key points in the expected output."),
            Rubric(score_range=(5, 8),  expected_outcome="Covers the main key points but misses one or more."),
            Rubric(score_range=(0, 4),  expected_outcome="Misses several key points; only partially covers the expected output."),
        ],
        evaluation_params=[LLMTestCaseParams.INPUT, LLMTestCaseParams.ACTUAL_OUTPUT, LLMTestCaseParams.EXPECTED_OUTPUT],
        threshold=THRESHOLD,
        model=judge,
        strict_mode=False,
    )

    # 4c. STYLE --- reference-free, judges TONE only (note: no EXPECTED_OUTPUT)
    style = GEval(
        name="Style",
        evaluation_steps=[
            "Judge only the teaching style and tone of the actual output, not whether it is factually correct or complete.",
            "Reward an intuitive, explanatory tone: plain language, the idea explained before any formula or jargon, and technical terms briefly unpacked when used.",
            "Reward a direct, conversational register written in prose, as a CampusX lecture would explain it out loud, rather than a dry, formal, or bullet-list tone.",
            "An analogy or concrete example is a BONUS when the concept is abstract, but a clear, direct, well-explained answer is fully acceptable and must NOT be penalized for not having one.",
            "Penalize answers that are stiff, bureaucratic, structured as a bare list with no explanation, or that use unexplained jargon.",
            "Do NOT reward or penalize based on correctness, completeness, or length --- only on style and tone.",
        ],
        rubric=[
            Rubric(score_range=(9, 10), expected_outcome="Clearly in a CampusX teaching voice: intuitive, conversational prose that explains before it formalizes."),
            Rubric(score_range=(7, 8),  expected_outcome="Clear, conversational, and well-explained in prose. Fully acceptable even without an analogy or example."),
            Rubric(score_range=(4, 6),  expected_outcome="Understandable but somewhat flat, formal, or list-heavy in places."),
            Rubric(score_range=(0, 3),  expected_outcome="Dry, stiff, bare-list, jargon-heavy, or robotic; does not read like a teaching explanation."),
        ],
        evaluation_params=[LLMTestCaseParams.INPUT, LLMTestCaseParams.ACTUAL_OUTPUT],
        threshold=THRESHOLD,
        model=judge,
        strict_mode=False,
    )

    # 5. EVALUATE --- teeno saath ma
    result = evaluate(
        test_cases=test_cases,
        metrics=[correctness, completeness, style],
        async_config=AsyncConfig(max_concurrent=MAX_CONCURRENT),
    )
    return summarize_by_metric(result)


def run_local():
    """Standalone convenience: pipeline banao, phir run karo."""
    return run(RagPipeline())


if __name__ == "__main__":
    print_summary("application", run_local())