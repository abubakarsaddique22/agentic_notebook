"""
Capstone evals — har change (prompt / model / retriever) se pehle chalao.

Chalao (09_capstone_support_bot folder se):
    python -m evals.run_evals --name baseline
    python -m evals.run_evals --name new-prompt --split edge-cases

Evaluators:
  - retrieval_hit   : sahi FAQ document retrieve hua?   (retriever quality)
  - concise         : 60 words se kam?                  (format)
  - no_invented_pay : fake payment method to nahi bataya? (safety/business rule)
  - correctness     : LLM-as-judge vs reference answer  (quality)
Summary:
  - retrieval_accuracy
"""
import argparse

from app.settings import APP_VERSION, EVAL_DATASET, JUDGE_MODEL, MODEL

from app.bot import respond
from langchain_groq import ChatGroq
# ---------------------------------------------------------
# ChatGroq  (class, langchain-groq) -- Groq ka LangChain chat model
#   LangChain ke andar Groq LLM: chain = prompt | ChatGroq(...) | parser.
#   LangChain runs LangSmith ma KHUD trace hote hain (env vars set hon to).
#   Attributes (constructor):
#     model            -> Groq model id (llama-3.3-70b-versatile, openai/gpt-oss-120b...)
#     temperature      -> 0 = sab se consistent jawab
#     max_tokens       -> jawab ki max lambai (None = model ka default)
#     reasoning_effort -> sirf reasoning models (gpt-oss): "low" | "medium" | "high"
#     reasoning_format -> "parsed" | "raw" | "hidden" -- reasoning kaise wapas aaye
#     timeout, max_retries -> network settings
#     api_key          -> na do to GROQ_API_KEY env var se
#   Methods: .invoke(), .stream(), .bind_tools([...]) (tool calling),
#            .with_structured_output(Schema) (JSON / pydantic output)
# ---------------------------------------------------------
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
from openevals.llm import create_llm_as_judge
from openevals.prompts import CORRECTNESS_PROMPT
# ---------------------------------------------------------
# create_llm_as_judge  (function, openevals) -- tayyar LLM-judge evaluator banata ha
#   Return: ek evaluator function -- client.evaluate(evaluators=[...]) ma do.
#   Arguments:
#     prompt       -> judge ka prompt ({inputs}, {outputs}, {reference_outputs} placeholders)
#     feedback_key -> score ka naam (UI ma column)
#     judge        -> LangChain model OBJECT (yahan ChatGroq) -- ya
#     model        -> string "provider:model" (jaise "groq:openai/gpt-oss-120b")
#     continuous   -> False = pass/fail (True/False), True = 0..1 score
#     choices      -> sirf ye scores allowed (jaise [0, 0.5, 1])
#     use_reasoning-> True = judge pehle reasoning likhe (comment ma dikhta ha)
#     few_shot_examples -> judge ko misaalein
#
# CORRECTNESS_PROMPT  (string, openevals) -- tayyar correctness judge prompt
#   Judge ko kehta ha: output ko reference_outputs (sahi jawab) se compare karo,
#   koi ghalat ya ulti baat ha? -> pass/fail + reasoning.
#   (openevals.prompts ma aur bhi hain: CONCISENESS_PROMPT, HALLUCINATION_PROMPT...)
# ---------------------------------------------------------


# ---------- Target ----------
def target(inputs: dict) -> dict:
    return respond(inputs["question"])  # {"answer", "sources"}


# ---------- Evaluators ----------
def retrieval_hit(outputs: dict, reference_outputs: dict) -> dict:
    expected = reference_outputs.get("expected_source")
    if expected is None:  # edge cases ka koi expected doc nahi
        return {"key": "retrieval_hit", "score": None}
    return {"key": "retrieval_hit", "score": expected in outputs["sources"]}


def concise(outputs: dict) -> bool:
    return len(outputs["answer"].split()) <= 60


def no_invented_pay(outputs: dict) -> dict:
    text = outputs["answer"].lower()
    claims = ["card accepted", "jazzcash available", "easypaisa available", "bank transfer kar"]
    bad = [c for c in claims if c in text]
    return {"key": "no_invented_pay", "score": not bad, "comment": ", ".join(bad) or "ok"}


correctness = create_llm_as_judge(
    prompt=CORRECTNESS_PROMPT,
    feedback_key="correctness",
    judge=ChatGroq(model=JUDGE_MODEL, temperature=0),
)


def correctness_eval(inputs: dict, outputs: dict, reference_outputs: dict):
    # Judge ko sirf answer text do (sources nahi)
    return correctness(
        inputs=inputs["question"],
        outputs=outputs["answer"],
        reference_outputs=reference_outputs["answer"],
    )


# ---------- Summary ----------
def retrieval_accuracy(outputs: list[dict], reference_outputs: list[dict]) -> dict:
    pairs = [(o, r) for o, r in zip(outputs, reference_outputs) if r.get("expected_source")]
    if not pairs:
        return {"key": "retrieval_accuracy", "score": None}
    hits = sum(r["expected_source"] in o["sources"] for o, r in pairs)
    return {"key": "retrieval_accuracy", "score": hits / len(pairs)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", default="run", help="experiment ka naam / change description")
    parser.add_argument("--split", default=None, help="sirf ek split par chalana, e.g. edge-cases")
    args = parser.parse_args()

    client = Client()
    data = (
        client.list_examples(dataset_name=EVAL_DATASET, splits=[args.split])
        if args.split
        else EVAL_DATASET
    )

    client.evaluate(
        target,
        data=data,
        evaluators=[retrieval_hit, concise, no_invented_pay, correctness_eval],
        summary_evaluators=[retrieval_accuracy],
        experiment_prefix=f"v{APP_VERSION}-{args.name}",
        metadata={"app_version": APP_VERSION, "model": MODEL, "judge_model": JUDGE_MODEL, "change": args.name},
        max_concurrency=4,
    )
