"""
Support bot ka core logic.

LangSmith concepts jo yahan use ho rahe hain:
  - @traceable + wrap_openai (Groq)    (folder 02)
  - retriever run type                 (folder 02, knowledge.py)
  - run_id control for feedback        (folder 08)
  - thread_id metadata -> Threads      (folder 04)
  - masked client (PII)                (folder 04, settings.py)
  - project per env + app_version      (folder 04, settings.py)
  - Prompt Hub + fallback              (folder 07, prompts.py)
  - runtime metadata                   (folder 02)
"""
import uuid
from dataclasses import dataclass, field

from app.settings import (
    COMMON_METADATA,
    GROQ_API_KEY,
    GROQ_BASE_URL,
    MAX_HISTORY_MESSAGES,
    MODEL,
    STORE_NAME,
    ls_client,
)

from app.knowledge import retrieve
from app.prompts import get_prompt
from langchain_core.messages import convert_to_openai_messages
# ---------------------------------------------------------
# convert_to_openai_messages  (langchain_core) -- LangChain messages ->
#   OpenAI format [{"role": ..., "content": ...}]. Groq bhi yahi format leta ha,
#   is liye Prompt Hub ka prompt OpenAI SDK (Groq URL) ke saath use ho jata ha.
# ---------------------------------------------------------
from langsmith import traceable
# ---------------------------------------------------------
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
from langsmith.run_helpers import get_current_run_tree
# ---------------------------------------------------------
# get_current_run_tree  (function) -- abhi chal raha run (RunTree) wapas deta ha
#   @traceable function ke andar call karo; bahar ho to None.
#   RunTree ke kaam ke methods:
#     run.add_metadata({...}) -> runtime pe metadata (jo pehle pata nahi tha)
#     run.add_tags([...])     -> runtime pe tags
#     run.to_headers()        -> HTTP headers -- doosri service isi trace ko aage chalaye
#     run.end(outputs=...)    -> run khatam + output set
#     run.id / run.trace_id   -> IDs
# ---------------------------------------------------------
from langsmith.wrappers import wrap_openai
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
from openai import OpenAI
# ---------------------------------------------------------
# OpenAI  (class) -- OpenAI ka Python SDK, lekin yahan GROQ ke liye use ho raha ha
#   Groq ka API OpenAI jaisa ha, is liye sirf do cheezein badalni hain:
#     base_url = "https://api.groq.com/openai/v1"
#     api_key  = GROQ_API_KEY  (.env se)
#   Baqi sab same: client.chat.completions.create(model=..., messages=[...])
#   Groq pe na chalne wale parameters: logprobs, logit_bias, top_logprobs, n>1.
#   temperature=0 Groq khud 1e-8 kar deta ha (koi masla nahi).
# ---------------------------------------------------------

oai = wrap_openai(OpenAI(base_url=GROQ_BASE_URL, api_key=GROQ_API_KEY), chat_name="ChatGroq")

# Demo ke liye memory mein. Production: Redis / Postgres.
_HISTORY: dict[str, list[dict]] = {}


@dataclass
class ChatResult:
    answer: str
    run_id: str
    sources: list[str] = field(default_factory=list)


@traceable(run_type="chain", name="Support Bot", client=ls_client)
def respond(question: str, history: list[dict] | None = None) -> dict:
    """Pure function: question (+history) -> answer. Evals bhi isi ko call karte hain."""
    docs = retrieve(question)
    context = "\n\n".join(d["page_content"] for d in docs) or "No relevant FAQ found."

    prompt, prompt_label = get_prompt()
    prompt_value = prompt.invoke({"store_name": STORE_NAME, "context": context, "question": question})
    messages = convert_to_openai_messages(prompt_value.to_messages())
    # system + (pichli baatein) + current question
    messages = messages[:1] + (history or []) + messages[1:]

    resp = oai.chat.completions.create(model=MODEL, messages=messages, temperature=0.2)
    answer = resp.choices[0].message.content

    # Runtime info trace mein (baad mein filter: "num_docs = 0" -> knowledge gaps!)
    run = get_current_run_tree()
    if run is not None:
        run.add_metadata({"prompt": prompt_label, "num_docs": len(docs)})
        if not docs:
            run.add_tags(["no-context"])

    return {"answer": answer, "sources": [d["metadata"]["id"] for d in docs]}


def chat(question: str, thread_id: str, user_id: str) -> ChatResult:
    """App ka entry point (API / CLI / WhatsApp webhook yahan call karein)."""
    run_id = uuid.uuid4()
    history = _HISTORY.setdefault(thread_id, [])

    out = respond(
        question,
        history[-MAX_HISTORY_MESSAGES:],
        langsmith_extra={
            "run_id": run_id,
            "metadata": {**COMMON_METADATA, "thread_id": thread_id, "user_id": user_id},
        },
    )

    history.append({"role": "user", "content": question})
    history.append({"role": "assistant", "content": out["answer"]})
    return ChatResult(answer=out["answer"], run_id=str(run_id), sources=out["sources"])


def record_feedback(run_id: str, score: int, comment: str | None = None) -> None:
    """User 👍 (1) / 👎 (0)."""
    ls_client.create_feedback(run_id, key="user_rating", score=score, comment=comment)
