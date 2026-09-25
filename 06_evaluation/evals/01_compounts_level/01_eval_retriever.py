# # # eval_retriever.py
# from dotenv import load_dotenv
# from src.reranker import RerankingRetriever
# from deepeval import evaluate
# from deepeval.test_case import LLMTestCase
# from deepeval.metrics import ContextualRecallMetric, ContextualPrecisionMetric


# from evals.harness import load_goldens, summarize_by_metric, print_summary

# load_dotenv()

# GOLDEN_PATH = "goldens/retriever_goldens.json"
# JUDGE_MODEL = "openai/gpt-oss-120b"   # NOTE: differs from the other evals (gpt-4o-mini)
# THRESHOLD = 0.7

# print("========================================")
# print("RETRIEVER EVALUATION STARTING")
# print("========================================")

# def run(retriever):
#     # 1. LOAD the golden set --- the fixed, human-authored truth
#     goldens = load_goldens(GOLDEN_PATH)
#     print(f"Loaded {len(goldens)} golden test cases from {GOLDEN_PATH}")
#     # 2. RUN THE INJECTED RETRIEVER on each question to fill retrieval_context,
#     #    then build one test case per golden.
#     test_cases = []
#     for g in goldens:
#         retrieved = retriever.invoke(g["query"])
#         retrieval_context = [doc.page_content for doc in retrieved]

#         test_cases.append(
#             LLMTestCase(
#                 input=g["query"],
#                 expected_output=g["ideal_answer"],
#                 retrieval_context=retrieval_context,
#                 actual_output="(generator not evaluated in this run)",
#             )
#         )

#     # 3. THE METRICS --- recall (did we miss?) and precision (ranked well?)
#     metrics = [
#         ContextualRecallMetric(threshold=THRESHOLD, model=JUDGE_MODEL, include_reason=True),
#         ContextualPrecisionMetric(threshold=THRESHOLD, model=JUDGE_MODEL, include_reason=True),
#     ]

#     # 4. EVALUATE --- every metric on every case, batched + parallel, printed report.
#     #    hyperparameters travel with the run so the report is tagged with the config.
#     result = evaluate(
#         test_cases=test_cases,
#         metrics=metrics,
#         hyperparameters={
#             "retriever": "reranker",
#             "embedding_model": "openai/text-embedding-3-large",
#             "chunk_size": 1000,
#             "chunk_overlap": 150,
#             "top_k": 3,
#             "judge_provider": "groq",
#             "judge_model": JUDGE_MODEL,
#             "golden_set": GOLDEN_PATH,
#     },
#     )
#     return summarize_by_metric(result)


# def run_local():
#     """Standalone convenience: build the retriever, then run."""
#     return run(RerankingRetriever())


# if __name__ == "__main__":
#     print_summary("retriever", run_local())

# ==================================================================
# using ollama 
# =======================================================================


# eval_retriever.py

# from dotenv import load_dotenv
# from src.reranker import RerankingRetriever

# from deepeval import evaluate
# from deepeval.test_case import LLMTestCase
# from deepeval.metrics import (
#     ContextualRecallMetric,
#     ContextualPrecisionMetric,
# )
# from deepeval.models import DeepEvalBaseLLM

# from ollama import Client

# from evals.harness import (
#     load_goldens,
#     summarize_by_metric,
#     print_summary,
# )


# load_dotenv()

# GOLDEN_PATH = "goldens/retriever_goldens.json"

# # Ollama judge model
# JUDGE_MODEL = "gpt-oss:20b-cloud"

# THRESHOLD = 0.7


# print("========================================")
# print("RETRIEVER EVALUATION STARTING")
# print("========================================")


# # =========================================================
# # OLLAMA JUDGE
# # =========================================================

# class OllamaJudge(DeepEvalBaseLLM):

#     def __init__(self, model):
#         self.model = model
#         self.client = Client(host="http://localhost:11434")

#     def load_model(self):
#         return self.client

#     def generate(self, prompt: str) -> str:

#         response = self.client.chat(
#             model=self.model,
#             messages=[
#                 {
#                     "role": "user",
#                     "content": prompt,
#                 }
#             ],
#         )

#         return response["message"]["content"]

#     async def a_generate(self, prompt: str) -> str:
#         return self.generate(prompt)

#     def get_model_name(self):
#         return self.model


# def run(retriever):

#     # =====================================================
#     # 1. LOAD GOLDEN SET
#     # =====================================================

#     goldens = load_goldens(GOLDEN_PATH)

#     print(
#         f"Loaded {len(goldens)} golden test cases "
#         f"from {GOLDEN_PATH}"
#     )


#     # =====================================================
#     # 2. RUN RETRIEVER
#     # =====================================================

#     test_cases = []

#     for g in goldens:

#         retrieved = retriever.invoke(g["query"])

#         retrieval_context = [
#             doc.page_content
#             for doc in retrieved
#         ]

#         test_cases.append(
#             LLMTestCase(
#                 input=g["query"],
#                 expected_output=g["ideal_answer"],
#                 retrieval_context=retrieval_context,
#                 actual_output="(generator not evaluated in this run)",
#             )
#         )


#     # =====================================================
#     # 3. CREATE OLLAMA JUDGE
#     # =====================================================

#     ollama_judge = OllamaJudge(
#         model=JUDGE_MODEL
#     )


#     # =====================================================
#     # 4. CREATE METRICS
#     # =====================================================

#     metrics = [

#         ContextualRecallMetric(
#             threshold=THRESHOLD,
#             model=ollama_judge,
#             include_reason=True,
#         ),

#         ContextualPrecisionMetric(
#             threshold=THRESHOLD,
#             model=ollama_judge,
#             include_reason=True,
#         ),

#     ]


#     # =====================================================
#     # 5. RUN DEEPEVAL
#     # =====================================================

#     result = evaluate(

#         test_cases=test_cases,

#         metrics=metrics,

#         hyperparameters={

#             "retriever": "reranker",

#             "embedding_model": "openai/text-embedding-3-large",

#             "chunk_size": 1000,

#             "chunk_overlap": 150,

#             "top_k": 3,

#             "judge_provider": "ollama",

#             "judge_model": JUDGE_MODEL,

#             "golden_set": GOLDEN_PATH,

#         },
#     )


#     # =====================================================
#     # 6. SUMMARY
#     # =====================================================

#     return summarize_by_metric(result)


# def run_local():
#     """Standalone convenience: build the retriever, then run."""

#     return run(
#         RerankingRetriever()
#     )


# if __name__ == "__main__":

#     print_summary(
#         "retriever",
#         run_local()
#     )


# eval_retriever.py
import re
import asyncio

from dotenv import load_dotenv
from openai import OpenAI, AsyncOpenAI
from pydantic import BaseModel

from src.reranker import RerankingRetriever

from deepeval import evaluate
from deepeval.evaluate.configs import AsyncConfig
from deepeval.test_case import LLMTestCase
from deepeval.metrics import (
    ContextualRecallMetric,
    ContextualPrecisionMetric,
)
from deepeval.models import DeepEvalBaseLLM

from evals.harness import (
    load_goldens,
    summarize_by_metric,
    print_summary,
)


load_dotenv()

GOLDEN_PATH = "goldens/retriever_goldens.json"

# Ollama cloud judge model (run once: ollama signin)
JUDGE_MODEL = "gpt-oss:20b-cloud"

# Ollama's OpenAI-compatible endpoint
OLLAMA_BASE_URL = "http://localhost:11434/v1"

THRESHOLD = 0.7


print("========================================")
print("RETRIEVER EVALUATION STARTING")
print("========================================")


# =========================================================
# OLLAMA JUDGE
# =========================================================

class OllamaJudge(DeepEvalBaseLLM):

    def __init__(self, model, base_url=OLLAMA_BASE_URL, max_retries: int = 3):
        self.model = model
        self.max_retries = max_retries

        # Ollama ignores the API key, but the OpenAI client needs one.
        self.client = OpenAI(
            api_key="ollama",
            base_url=base_url,
        )
        self.async_client = AsyncOpenAI(
            api_key="ollama",
            base_url=base_url,
        )

    def load_model(self):
        return self.client

    def _build_kwargs(self, prompt: str, schema):

        kwargs = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            "temperature": 0,
            "max_tokens": 8000,
            "reasoning_effort": "low",
        }

        # DeepEval gives us a Pydantic schema.
        # Ask Ollama to return exactly that JSON structure.
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

    @staticmethod
    def _parse(content: str, schema):

        if schema is None:
            return content

        # strip ```json fences if the model added them
        cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", content.strip())

        # DeepEval expects a Pydantic object
        # when schema is provided.
        return schema.model_validate_json(cleaned)

    @staticmethod
    def _extract(response):

        choice = response.choices[0]
        content = choice.message.content

        if not content:
            raise ValueError(
                f"Ollama returned an empty response "
                f"(finish_reason={choice.finish_reason})"
            )

        return content

    def generate(
        self,
        prompt: str,
        schema: BaseModel | None = None,
    ):

        last_err = None

        for attempt in range(self.max_retries):
            try:
                response = self.client.chat.completions.create(
                    **self._build_kwargs(prompt, schema)
                )
                return self._parse(self._extract(response), schema)

            except Exception as e:
                last_err = e

        raise ValueError(f"Judge failed after retries: {last_err}")

    async def a_generate(
        self,
        prompt: str,
        schema: BaseModel | None = None,
    ):

        last_err = None

        for attempt in range(self.max_retries):
            try:
                response = await self.async_client.chat.completions.create(
                    **self._build_kwargs(prompt, schema)
                )
                return self._parse(self._extract(response), schema)

            except Exception as e:
                last_err = e
                await asyncio.sleep(2 ** attempt)

        raise ValueError(f"Judge failed after retries: {last_err}")

    def get_model_name(self):
        return self.model





def run(retriever):

    # =====================================================
    # 1. LOAD GOLDEN SET
    # =====================================================

    goldens = load_goldens(GOLDEN_PATH)

    print(
        f"Loaded {len(goldens)} golden test cases "
        f"from {GOLDEN_PATH}"
    )


    # =====================================================
    # 2. RUN RETRIEVER
    # =====================================================

    test_cases = []

    for g in goldens:

        retrieved = retriever.invoke(g["query"])

        retrieval_context = [
            doc.page_content
            for doc in retrieved
        ]

        test_cases.append(
            LLMTestCase(
                input=g["query"],
                expected_output=g["ideal_answer"],
                retrieval_context=retrieval_context,
                actual_output="(generator not evaluated in this run)",
            )
        )


    # =====================================================
    # 3. CREATE OLLAMA JUDGE
    # =====================================================

    judge = OllamaJudge(
        model=JUDGE_MODEL
    )


    # =====================================================
    # 4. CREATE METRICS
    # =====================================================

    metrics = [

        ContextualRecallMetric(
            threshold=THRESHOLD,
            model=judge,
            include_reason=True,
        ),

        ContextualPrecisionMetric(
            threshold=THRESHOLD,
            model=judge,
            include_reason=True,
        ),

    ]


    # =====================================================
    # 5. RUN DEEPEVAL
    # =====================================================

    result = evaluate(

        test_cases=test_cases,

        metrics=metrics,

        async_config=AsyncConfig(max_concurrent=2),

        hyperparameters={

            "retriever": "reranker",

            "embedding_model": "openai/text-embedding-3-large",

            "chunk_size": 1000,

            "chunk_overlap": 150,

            "top_k": 3,

            "judge_provider": "ollama",

            "judge_model": JUDGE_MODEL,

            "golden_set": GOLDEN_PATH,

        },
    )
 

    # =====================================================
    # 6. SUMMARY
    # =====================================================

    return summarize_by_metric(result)


def run_local():
    """Standalone convenience: build the retriever, then run."""

    return run(
        RerankingRetriever()
    )


if __name__ == "__main__":

    print_summary(
        "retriever",
        run_local()
    )