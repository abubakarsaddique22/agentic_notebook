"""
Prompt pull karke use karna.

Identifier formats:
  "watch-support-prompt"            -> latest commit
  "watch-support-prompt:<commit>"   -> specific commit hash (UI se copy)
  "watch-support-prompt:prod"       -> jis commit par 'prod' tag hai (UI mein lagao)

Industry pattern: startup par pull + cache, fail ho to local fallback.
"""
import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from langchain_core.messages import convert_to_openai_messages  # noqa: E402
# ---------------------------------------------------------
# convert_to_openai_messages  (langchain_core) -- LangChain messages ->
#   OpenAI format [{"role": ..., "content": ...}]. Groq bhi yahi format leta ha,
#   is liye Prompt Hub ka prompt OpenAI SDK (Groq URL) ke saath use ho jata ha.
# ---------------------------------------------------------
from langchain_core.prompts import ChatPromptTemplate  # noqa: E402
# ---------------------------------------------------------
# ChatPromptTemplate  (langchain_core) -- placeholders wala chat prompt
#   from_messages([("system", "...{var}..."), ("human", "{question}")])
#   .invoke({vars}) -> PromptValue; LangSmith Prompt Hub pe isi ko push / pull karte hain.
# ---------------------------------------------------------
from langchain_groq import ChatGroq  # noqa: E402
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
from langsmith import Client, traceable  # noqa: E402
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
#
# traceable  (decorator) -- function ko LangSmith ka "run" (span) bana deta ha
#   Function ka input, output, time, error -- sab trace ma. Andar se doosra
#   @traceable function call ho to wo CHILD run ban jata ha (tree banta ha).
#   Sync, async aur generator -- sab functions pe kaam karta ha.
#   Decorator arguments:
#     name           -> run ka naam (default: function ka naam)
#     run_type       -> "chain" (default) | "llm" | "tool" | "retriever" | "prompt" | "parser"
#                       -- UI isi ke hisaab se run ko dikhata ha (retriever = documents list)
#     tags           -> list of strings, filter karne ke liye
#     metadata       -> dict (version, user_id...), filter + compare ke liye
#     client         -> kaunsa langsmith Client traces bheje (masking / flush ke liye)
#     project_name   -> is function ke runs kis project ma jayen
#     process_inputs / process_outputs -> trace ma jaane se pehle data badlo
#     enabled        -> is function ki tracing on/off
#   Call ke waqt extra: fn(..., langsmith_extra={...})
#     metadata, tags, run_id (apni uuid -- feedback ke liye), project_name,
#     parent, client, name
#   Tracing tabhi hoti ha jab .env ma LANGSMITH_TRACING=true ho.
# ---------------------------------------------------------
from langsmith.wrappers import wrap_openai  # noqa: E402
# ---------------------------------------------------------
# wrap_openai  (function) -- OpenAI SDK client ki AUTOMATIC tracing
#   wrap_openai(client) ek naya client deta ha jis ki har chat.completions.create
#   call khud "llm" run ban jati ha: messages, model, tokens, latency, streaming.
#   Groq ka apna LangSmith wrapper nahi ha -- lekin Groq OpenAI-compatible ha,
#   is liye OpenAI SDK (base_url = Groq) + wrap_openai = poori tracing.
#   Arguments:
#     client        -> OpenAI() ya AsyncOpenAI() object
#     chat_name     -> trace ma LLM run ka naam (default "ChatOpenAI"; yahan "ChatGroq")
#     tracing_extra -> {"metadata", "tags", "client"} -- har call pe lagne wali extra info
#   NOTE: tokens hamesha dikhte hain; COST tabhi jab LangSmith ke Settings ->
#   Model Pricing ma Groq model ka rate add karo (warna $0 dikhega).
# ---------------------------------------------------------
from openai import OpenAI  # noqa: E402
# ---------------------------------------------------------
# OpenAI  (class) -- OpenAI ka Python SDK, lekin yahan GROQ ke liye use ho raha ha
#   Groq ka API OpenAI jaisa ha, is liye sirf do cheezein badalni hain:
#     base_url = "https://api.groq.com/openai/v1"
#     api_key  = GROQ_API_KEY  (.env se)
#   Baqi sab same: client.chat.completions.create(model=..., messages=[...])
#   Groq pe na chalne wale parameters: logprobs, logit_bias, top_logprobs, n>1.
#   temperature=0 Groq khud 1e-8 kar deta ha (koi masla nahi).
# ---------------------------------------------------------

# Groq OpenAI-compatible endpoint -- OpenAI SDK hi use hota ha, sirf URL + key Groq ki
GROQ_BASE_URL = "https://api.groq.com/openai/v1"
MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
PROMPT_ID = os.getenv("SUPPORT_PROMPT_ID", "watch-support-prompt")  # prod mein ":prod" lagao

FAQ = "Delivery 1-2 din (Lahore). Sirf COD. 7 din exchange. 6 mahine warranty."
VARS = {"store_name": "Watch Store", "faq": FAQ}

FALLBACK_PROMPT = ChatPromptTemplate.from_messages(
    [("system", "You are a support agent for {store_name}. FAQ:\n{faq}"), ("human", "{question}")]
)


@lru_cache(maxsize=1)
def load_prompt() -> ChatPromptTemplate:
    try:
        prompt = Client().pull_prompt(PROMPT_ID)
        print(f"Hub se prompt load hua: {PROMPT_ID}")
        return prompt
    except Exception as e:
        print(f"Hub fail ({e}) -> local fallback use ho raha hai")
        return FALLBACK_PROMPT


# ---------- Use 1: LangChain ke saath ----------
def answer_with_langchain(question: str) -> str:
    chain = load_prompt() | ChatGroq(model=MODEL, temperature=0)
    msg = chain.invoke(
        {**VARS, "question": question},
        config={"metadata": {"prompt_id": PROMPT_ID}},  # version trace mein
    )
    return msg.content


# ---------- Use 2: Plain OpenAI SDK ke saath (Groq URL) ----------
oai = wrap_openai(OpenAI(base_url=GROQ_BASE_URL, api_key=os.getenv("GROQ_API_KEY")), chat_name="ChatGroq")


@traceable(name="Answer With OpenAI SDK", metadata={"prompt_id": PROMPT_ID})
def answer_with_openai(question: str) -> str:
    prompt_value = load_prompt().invoke({**VARS, "question": question})
    messages = convert_to_openai_messages(prompt_value.to_messages())
    resp = oai.chat.completions.create(model=MODEL, messages=messages, temperature=0)
    return resp.choices[0].message.content


if __name__ == "__main__":
    print("LangChain :", answer_with_langchain("Card se payment ho sakti hai?"))
    print("OpenAI SDK:", answer_with_openai("Warranty kitni hai?"))
