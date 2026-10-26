"""
Decorator ke ilawa tracing ke tareeqe:

  1. ls.trace(...)          -> code ke ek block ko run banana
  2. get_current_run_tree() -> chalte hue run mein runtime par metadata/tags add karna
  3. ls.tracing_context()   -> kisi block ka project/metadata badalna, ya tracing OFF karna
"""
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

import langsmith as ls  # noqa: E402
# ---------------------------------------------------------
# import langsmith as ls  -- poora package (yahan ls.trace / ls.tracing_context ke liye)
#   ls.trace(name, run_type, inputs, tags, metadata, project_name, parent)
#       -> `with` block ko ek run banata ha (decorator ke bina). Andar run.end(outputs=...)
#   ls.tracing_context(project_name, tags, metadata, parent, enabled, client)
#       -> `with` block ke andar ke SAARE traces pe settings lagao:
#          alag project, extra metadata, parent=headers (distributed tracing),
#          ya enabled=False (tracing band).
# ---------------------------------------------------------
from langsmith import traceable  # noqa: E402
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
from langsmith.run_helpers import get_current_run_tree  # noqa: E402
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


@traceable(name="Classify Intent")
def classify_intent(text: str) -> str:
    intent = "order_status" if "order" in text.lower() else "general"

    # Runtime par current run mein info add karo (jo pehle se pata nahi thi)
    run = get_current_run_tree()
    if run is not None:
        run.add_metadata({"detected_intent": intent})
        run.add_tags([f"intent:{intent}"])
    return intent


def process_batch(messages: list[str]) -> list[str]:
    # 1) ls.trace: jab poore function ko decorate nahi karna, sirf ek block trace karna hai
    with ls.trace(
        name="Batch Processing",
        run_type="chain",
        inputs={"count": len(messages)},
        tags=["batch"],
    ) as run:
        results = [classify_intent(m) for m in messages]
        run.end(outputs={"intents": results})  # output khud set karo
    return results


if __name__ == "__main__":
    print(process_batch(["Mera order kahan hai?", "Shop kab khulti hai?"]))

    # 2) tracing_context: is block ke traces ALAG project mein + extra metadata ke saath
    with ls.tracing_context(
        project_name="langsmith-learning-experiments",
        metadata={"experiment": "context-demo"},
    ):
        classify_intent("order cancel karna hai")

    # 3) Tracing OFF — e.g. health checks, unit tests, ya sensitive code
    with ls.tracing_context(enabled=False):
        classify_intent("yeh trace NAHI hoga")

    print("UI: 'langsmith-learning-experiments' naam ka naya project bhi check karo.")
