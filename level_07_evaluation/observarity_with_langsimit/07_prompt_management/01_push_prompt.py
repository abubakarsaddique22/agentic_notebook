"""
Prompt ko LangSmith Prompt Hub par push karna.

Prompt naam: lowercase + hyphens (e.g. "watch-support-prompt").
Har push = naya commit. Same content dobara push karo to error aata hai (kuch change nahi hua).
"""
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from langchain_core.prompts import ChatPromptTemplate  # noqa: E402
# ---------------------------------------------------------
# ChatPromptTemplate  (langchain_core) -- placeholders wala chat prompt
#   from_messages([("system", "...{var}..."), ("human", "{question}")])
#   .invoke({vars}) -> PromptValue; LangSmith Prompt Hub pe isi ko push / pull karte hain.
# ---------------------------------------------------------
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

PROMPT_NAME = "watch-support-prompt"

PROMPT_V1 = ChatPromptTemplate.from_messages(
    [
        ("system", "You are a support agent for {store_name}. Answer using this FAQ:\n{faq}"),
        ("human", "{question}"),
    ]
)

PROMPT_V2 = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are the customer support agent of {store_name}.\n"
            "Rules: answer ONLY from the FAQ, reply in Roman Urdu, max 2 sentences, "
            "politely refuse non-store questions.\n\nFAQ:\n{faq}",
        ),
        ("human", "{question}"),
    ]
)


def push(client: Client, prompt: ChatPromptTemplate, label: str) -> None:
    try:
        url = client.push_prompt(
            PROMPT_NAME,
            object=prompt,
            description="Watch store support bot system prompt",
            tags=["support-bot"],
        )
        print(f"[{label}] pushed -> {url}")
    except Exception as e:  # e.g. "Nothing to commit" agar content same hai
        print(f"[{label}] skip: {e}")


if __name__ == "__main__":
    client = Client()
    push(client, PROMPT_V1, "v1")
    push(client, PROMPT_V2, "v2")
    print("\nUI: Prompts -> watch-support-prompt -> Commits. Latest commit par 'prod' tag lagao.")
