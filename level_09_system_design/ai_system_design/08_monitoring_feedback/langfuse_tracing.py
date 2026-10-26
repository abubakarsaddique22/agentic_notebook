"""
Module 8 · Real observability with Langfuse (optional, free cloud tier ya self-host)
====================================================================================

M9.7 wali SupportPipeline ko Langfuse se instrument karta hai:
  - har request = 1 TRACE (user_id hashed, session_id, version, tags)
  - andar SPANS: classify, retrieve (retriever), llm (generation: model + tokens)
  - user feedback = SCORE on the trace
  - thumbs-down trace -> DATASET item (regression eval set, Level 7 se link)

Setup (ek dafa):
  1. https://cloud.langfuse.com par free account -> project -> API keys
  2. .env mein:
        LANGFUSE_PUBLIC_KEY=pk-lf-...
        LANGFUSE_SECRET_KEY=sk-lf-...
        LANGFUSE_HOST=https://cloud.langfuse.com
  3. pip install langfuse

Chalane ka tareeqa (PowerShell, root folder, venv active):
    python 08_monitoring_feedback\\langfuse_tracing.py
Phir Langfuse UI mein Traces, Scores aur Datasets tab dekho.

Langfuse SDK v3+ (OpenTelemetry based) API use hui hai: get_client, start_as_current_observation,
propagate_attributes, create_score, create_dataset_item. (v5.0 par test kiya)
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "07_pipeline_orchestration"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
load_dotenv(ROOT / ".env")
load_dotenv()

APP_VERSION, PROMPT_VERSION, RETRIEVAL_CONFIG = "v1.5", "support-v3", "keyword-k2"
DATASET = "support-regressions"


def main() -> None:
    if not (os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY")):
        print("LANGFUSE_PUBLIC_KEY / LANGFUSE_SECRET_KEY .env mein nahi mili.")
        print("Setup steps is file ke upar likhe hain. Tab tak monitoring_lab.py (offline) chalao.")
        return

    from langfuse import get_client, propagate_attributes

    from components import (FakeShopifyOrders, KeywordRetriever, RuleIntentClassifier,  # noqa
                            default_llm, SYSTEM)
    from tracer import hash_user

    lf = get_client()
    if not lf.auth_check():
        print("Langfuse auth fail: keys / host check karein.")
        return

    classifier, retriever, llm, orders = (RuleIntentClassifier(), KeywordRetriever(),
                                          default_llm(), FakeShopifyOrders())
    try:
        lf.create_dataset(name=DATASET, description="Production failures -> regression evals")
    except Exception:  # noqa: BLE001  (pehle se bana ho to theek hai)
        pass

    conversations = [
        ("923001111111", "Return policy kya hai?", +1),
        ("923002222222", "Delivery charges kitne hain?", +1),
        ("923003333333", "Kya aap Dubai bhejte ho?", -1),     # bot ke paas info nahi -> thumbs down
    ]

    for phone, text, user_feedback in conversations:
        with propagate_attributes(user_id=hash_user(phone), session_id=f"wa-{hash_user(phone)}",
                                  version=APP_VERSION, tags=[PROMPT_VERSION, RETRIEVAL_CONFIG],
                                  metadata={"channel": "whatsapp", "tenant": "tussles_demo"},
                                  trace_name="support-request"):
            with lf.start_as_current_observation(name="support-request", as_type="chain",
                                                 input={"text": text}) as root:
                with lf.start_as_current_observation(name="classify", as_type="span",
                                                     input=text) as s:
                    intent = classifier.classify(text)
                    s.update(output=intent)

                with lf.start_as_current_observation(name="retrieve", as_type="retriever",
                                                     input=text,
                                                     metadata={"config": RETRIEVAL_CONFIG}) as s:
                    docs = retriever.search(text)
                    s.update(output=[d["id"] for d in docs])

                ctx = "\n".join(f"[{d['id']}] {d['text']}" for d in docs) or "(no data)"
                user_msg = f"Data:\n{ctx}\n\nCustomer: {text}"
                with lf.start_as_current_observation(
                        name="llm-answer", as_type="generation", model="groq/openai/gpt-oss-20b",
                        input=[{"role": "system", "content": SYSTEM},
                               {"role": "user", "content": user_msg}],
                        model_parameters={"reasoning_effort": "low", "temperature": 0.2},
                        metadata={"prompt_version": PROMPT_VERSION}) as gen:
                    answer = llm.generate(SYSTEM, user_msg)
                    # Real Groq usage ke liye response.usage se tokens lo; yahan rough estimate
                    gen.update(output=answer, usage_details={"input": len(user_msg) // 4,
                                                             "output": len(answer) // 4})

                root.update(output={"reply": answer, "intent": intent})
                trace_id = lf.get_current_trace_id()

        # ---- Feedback aata hai baad mein (WhatsApp button / reaction) ----
        lf.create_score(trace_id=trace_id, name="user_feedback", value=user_feedback,
                        data_type="NUMERIC", comment="thumbs from WhatsApp")
        if user_feedback < 0:
            lf.create_dataset_item(dataset_name=DATASET, input={"text": text},
                                   expected_output=None,        # human baad mein bharega
                                   source_trace_id=trace_id,
                                   metadata={"app_version": APP_VERSION,
                                             "prompt_version": PROMPT_VERSION})
        try:
            where = lf.get_trace_url(trace_id=trace_id)
        except Exception:  # noqa: BLE001  (URL ke liye network call hoti hai)
            where = f"trace_id={trace_id}"
        print(f"traced: {text!r:34} feedback={user_feedback:+d} -> {where}")

    lf.flush()
    print(f"\nDone. Langfuse UI: Traces, Scores, aur Datasets > {DATASET} dekho.")


if __name__ == "__main__":
    main()
