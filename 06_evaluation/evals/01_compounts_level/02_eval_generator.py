# """
# evals/eval_generator.py
# =======================
# Component-level evaluation of the GENERATOR, in isolation.

# Faithfulness: of the claims in the generated answer, how many are supported
# by the context it was given? (Did the generator make things up?)

# ISOLATION: we feed the generator the GOLDEN context (the known-good chunks
# from the faithfulness dataset), NOT the retriever's output. So a low score
# is purely the generator's fault --- the context was already correct.

#     python -m evals.eval_generator
# """

# from dotenv import load_dotenv

# from deepeval import evaluate
# from deepeval.test_case import LLMTestCase
# from deepeval.metrics import FaithfulnessMetric, AnswerRelevancyMetric

# from src.generator import generate   # your generator: generate(query, context) -> answer
# from evals.harness import load_goldens, summarize_by_metric, print_summary


# # ja cheezs import just for ollama ka laii hai agra hum openai use karta tu bht simple code hotaa

# import re
# import asyncio

# from dotenv import load_dotenv
# from openai import OpenAI, AsyncOpenAI
# from pydantic import BaseModel

# from deepeval.models import DeepEvalBaseLLM
# from deepeval.evaluate.configs import AsyncConfig

# load_dotenv()

# GOLDEN_PATH = "goldens/faithfulness_dataset.json"
# # Ollama cloud judge model (run once: ollama signin)
# JUDGE_MODEL = "gpt-oss:20b-cloud"

# # Ollama's OpenAI-compatible endpoint
# OLLAMA_BASE_URL = "http://localhost:11434/v1"

# THRESHOLD = 0.7



# # =========================================================
# # OLLAMA JUDGE
# # =========================================================

# class OllamaJudge(DeepEvalBaseLLM):

#     def __init__(self, model, base_url=OLLAMA_BASE_URL, max_retries: int = 3):
#         self.model = model
#         self.max_retries = max_retries

#         # Ollama ignores the API key, but the OpenAI client needs one.
#         self.client = OpenAI(
#             api_key="ollama",
#             base_url=base_url,
#         )
#         self.async_client = AsyncOpenAI(
#             api_key="ollama",
#             base_url=base_url,
#         )

#     def load_model(self):
#         return self.client

#     def _build_kwargs(self, prompt: str, schema):

#         kwargs = {
#             "model": self.model,
#             "messages": [
#                 {
#                     "role": "user",
#                     "content": prompt,
#                 }
#             ],
#             "temperature": 0,
#             "max_tokens": 8000,
#             "reasoning_effort": "low",
#         }

#         # DeepEval gives us a Pydantic schema.
#         # Ask Ollama to return exactly that JSON structure.
#         if schema is not None:

#             kwargs["response_format"] = {
#                 "type": "json_schema",
#                 "json_schema": {
#                     "name": "deepeval_output",
#                     "strict": False,
#                     "schema": schema.model_json_schema(),
#                 },
#             }

#         return kwargs

#     @staticmethod
#     def _parse(content: str, schema):

#         if schema is None:
#             return content

#         # strip ```json fences if the model added them
#         cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", content.strip())

#         # DeepEval expects a Pydantic object
#         # when schema is provided.
#         return schema.model_validate_json(cleaned)

#     @staticmethod
#     def _extract(response):

#         choice = response.choices[0]
#         content = choice.message.content

#         if not content:
#             raise ValueError(
#                 f"Ollama returned an empty response "
#                 f"(finish_reason={choice.finish_reason})"
#             )

#         return content

#     def generate(
#         self,
#         prompt: str,
#         schema: BaseModel | None = None,
#     ):

#         last_err = None

#         for attempt in range(self.max_retries):
#             try:
#                 response = self.client.chat.completions.create(
#                     **self._build_kwargs(prompt, schema)
#                 )
#                 return self._parse(self._extract(response), schema)

#             except Exception as e:
#                 last_err = e

#         raise ValueError(f"Judge failed after retries: {last_err}")

#     async def a_generate(
#         self,
#         prompt: str,
#         schema: BaseModel | None = None,
#     ):

#         last_err = None

#         for attempt in range(self.max_retries):
#             try:
#                 response = await self.async_client.chat.completions.create(
#                     **self._build_kwargs(prompt, schema)
#                 )
#                 return self._parse(self._extract(response), schema)

#             except Exception as e:
#                 last_err = e
#                 await asyncio.sleep(2 ** attempt)

#         raise ValueError(f"Judge failed after retries: {last_err}")

#     def get_model_name(self):
#         return self.model




# def run():
#     # 1. LOAD the faithfulness golden set (query + ideal_context)
#     goldens = load_goldens(GOLDEN_PATH)

#     # 2. RUN THE GENERATOR on the GOLDEN context (isolation), build one test case each
#     test_cases = []
#     for g in goldens:
#         context = g["ideal_context"]              # known-good context (list of chunk strings)
#         answer = generate(g["query"], context)    # RUN the generator -> actual_output

#         test_cases.append(
#             LLMTestCase(
#                 input=g["query"],
#                 actual_output=answer,             # the generated answer we're judging
#                 retrieval_context=context,        # faithfulness checks the answer against THIS
#                 # no expected_output --- faithfulness never reads it
#             )
#         )

#      # =====================================================
#         # 3. CREATE OLLAMA JUDGE
#         # =====================================================
    
#         judge = OllamaJudge(
#             model=JUDGE_MODEL
#         )

#     # 3. THE METRICS --- decompose actual_output into claims, attribute each to context
#     metrics = [
#         FaithfulnessMetric(
#             threshold=THRESHOLD,
#             model=judge,
#             include_reason=True,   # prints WHY each score --- shows which claims were unsupported
#         ),
#         AnswerRelevancyMetric(
#             threshold=THRESHOLD,
#             model=judge,
#             include_reason=True,
#         ),
#     ]

#     # 4. EVALUATE --- runs the metrics on every case, prints a report
#     result = evaluate(
#         test_cases=test_cases, 
#         metrics=metrics,
#         async_config=AsyncConfig(max_concurrent=2))
#     return summarize_by_metric(result)


# if __name__ == "__main__":
#     print_summary("generator", run())





import re
import asyncio

import json_repair
from dotenv import load_dotenv
from openai import OpenAI, AsyncOpenAI
from pydantic import BaseModel

from deepeval import evaluate
from deepeval.evaluate.configs import AsyncConfig
from deepeval.test_case import LLMTestCase
from deepeval.metrics import FaithfulnessMetric, AnswerRelevancyMetric
from deepeval.models import DeepEvalBaseLLM

from src.generator import generate   # generate(query, context) -> answer
from evals.harness import load_goldens, summarize_by_metric, print_summary

load_dotenv()

GOLDEN_PATH = "goldens/faithfulness_dataset.json"
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

def run():
    # 1. LOAD golden set (query + ideal_context)
    goldens = load_goldens(GOLDEN_PATH)
    print(f"Loaded {len(goldens)} golden test cases from {GOLDEN_PATH}")

    # 2. RUN GENERATOR on GOLDEN context (isolation), one test case each
    test_cases = []
    for g in goldens:
        context = g["ideal_context"]              # list of chunk strings
        answer = generate(g["query"], context)    # actual_output

        test_cases.append(
            LLMTestCase(
                input=g["query"],
                actual_output=answer,
                retrieval_context=context,        # faithfulness answer ko isi se check karta ha
            )
        )

    # 3. JUDGE: sirf ek dafa, loop ke BAHAR
    judge = OllamaJudge(model=JUDGE_MODEL)

    # 4. METRICS
    metrics = [
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


if __name__ == "__main__":
    print_summary("generator", run())