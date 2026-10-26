"""
LLM-as-judge: doosra LLM tumhare output ko grade karta hai.

1. CORRECTNESS judge (reference answer se compare)
2. Apna custom judge — tumhare business rules ke hisaab se (tone + hallucination)

Judge: Ollama Cloud (gpt-oss:20b-cloud) -- local Ollama app ke through.
Bot (target): Groq par hi hai (support_app).

NOTE: openevals ka create_llm_as_judge OpenAI client ke saath strict JSON-schema
mangta ha, jo Ollama + gpt-oss par aksar khaali / adhoora JSON deta ha. Is liye
dono judges yahan "json_object" mode se bane hain (jo Ollama par theek chalta ha)
aur ek retry wala helper (ask_judge) use karte hain.

Tip: Judge prompt ko bhi version karo aur kabhi kabhi human labels se check karo
ke judge khud sahi grade kar raha hai ya nahi.
"""
import json
import os

from support_app import support_bot

from langsmith import Client
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
from langsmith.wrappers import wrap_openai
# ---------------------------------------------------------
# wrap_openai  (function) -- OpenAI SDK client ki AUTOMATIC tracing
#   wrap_openai(client) ek naya client deta ha jis ki har chat.completions.create
#   call khud "llm" run ban jati ha: messages, model, tokens, latency, streaming.
#   Ollama bhi OpenAI-compatible ha, is liye OpenAI SDK (base_url = Ollama)
#   + wrap_openai = poori tracing.
#   Arguments:
#     client        -> OpenAI() ya AsyncOpenAI() object
#     chat_name     -> trace ma LLM run ka naam (yahan "OllamaJudge")
#     tracing_extra -> {"metadata", "tags", "client"} -- har call pe lagne wali extra info
# ---------------------------------------------------------
from openai import OpenAI
# ---------------------------------------------------------
# OpenAI  (class) -- OpenAI ka Python SDK, lekin yahan OLLAMA ke liye use ho raha ha
#   Ollama ka API OpenAI jaisa ha, is liye sirf do cheezein badalni hain:
#     base_url = "http://localhost:11434/v1"   (local Ollama app)
#     api_key  = "ollama"  (koi bhi string chalegi, Ollama check nahi karta)
#   "-cloud" wale models local app ke through Ollama ke servers par chalte hain
#   (pehle `ollama signin` zaroori).
# ---------------------------------------------------------

DATASET_NAME = "watch-support-qa"
# Judge Ollama Cloud par (app wale Groq model se alag -- Groq ki rate limit bhi bachti ha)
OLLAMA_BASE_URL = "http://localhost:11434/v1"
JUDGE_MODEL = os.getenv("OLLAMA_JUDGE_MODEL", "gpt-oss:20b-cloud")
judge_client = wrap_openai(OpenAI(base_url=OLLAMA_BASE_URL, api_key="ollama"), chat_name="OllamaJudge")


def target(inputs: dict) -> dict:
    return {"answer": support_bot(inputs["question"], prompt_version="v2")}


# ---------- Helper: judge se JSON lo (retry ke saath) ----------
def ask_judge(prompt: str, retries: int = 2) -> dict | None:
    """Judge ko prompt bhejo aur JSON dict wapas lo.
    Khaali ya ghalat JSON aaye to dobara try karo. Phir bhi na mile to None."""
    for _ in range(retries + 1):
        resp = judge_client.chat.completions.create(
            model=JUDGE_MODEL,
            temperature=0,
            response_format={"type": "json_object"},
            messages=[{"role": "user", "content": prompt}],
        )
        content = (resp.choices[0].message.content or "").strip()
        try:
            data = json.loads(content)
            if isinstance(data, dict):  # sirf {...} chahiye, akela number / list nahi
                return data
        except json.JSONDecodeError:
            pass
    return None


# ---------- 1) Correctness judge ----------
CORRECTNESS_JUDGE_PROMPT = """You are an expert grader for a watch store customer-support bot.
Compare the bot reply with the reference answer.

Customer question: {question}
Reference answer: {reference}
Bot reply: {answer}

The reply is CORRECT if it gives the same key facts as the reference and does not
contradict it. Different wording is fine (Roman Urdu or English). Extra polite words are fine.
The reply is INCORRECT if any fact is wrong, missing in a way that changes the meaning,
or contradicts the reference.

Return JSON: {{"correct": bool, "reasoning": "one sentence"}}"""


def correctness_judge(inputs: dict, outputs: dict, reference_outputs: dict) -> dict:
    verdict = ask_judge(
        CORRECTNESS_JUDGE_PROMPT.format(
            question=inputs["question"],
            reference=reference_outputs["answer"],
            answer=outputs["answer"],
        )
    )
    if verdict is None:
        return {"key": "correctness", "score": None, "comment": "Judge ne valid JSON nahi diya"}
    return {
        "key": "correctness",
        "score": bool(verdict.get("correct")),
        "comment": verdict.get("reasoning", ""),
    }


# ---------- 2) Custom judge ----------
CUSTOM_JUDGE_PROMPT = """You are grading a customer-support reply for a watch store.

Customer question: {question}
Reference answer: {reference}
Bot reply: {answer}

Check:
- grounded: Does the reply avoid inventing any fact not in the reference? (true/false)
- polite: Is the tone polite and professional? (true/false)

Return JSON: {{"grounded": bool, "polite": bool, "reasoning": "one sentence"}}"""


def custom_judge(inputs: dict, outputs: dict, reference_outputs: dict) -> dict:
    verdict = ask_judge(
        CUSTOM_JUDGE_PROMPT.format(
            question=inputs["question"],
            reference=reference_outputs["answer"],
            answer=outputs["answer"],
        )
    )
    if verdict is None:
        return {
            "results": [
                {"key": "grounded", "score": None, "comment": "Judge ne valid JSON nahi diya"},
                {"key": "polite", "score": None},
            ]
        }
    # Ek evaluator se multiple scores: {"results": [ ... ]}
    return {
        "results": [
            {"key": "grounded", "score": bool(verdict.get("grounded")), "comment": verdict.get("reasoning", "")},
            {"key": "polite", "score": bool(verdict.get("polite"))},
        ]
    }


if __name__ == "__main__":
    client = Client()
    client.evaluate(
        target,
        data=DATASET_NAME,
        evaluators=[correctness_judge, custom_judge],
        experiment_prefix="llm-judge-v2",
        metadata={"prompt_version": "v2", "judge_model": JUDGE_MODEL},
        max_concurrency=4,
    )
    print("UI: experiment kholo -> har score par click karo -> judge ka 'comment' (reasoning) dekho.")