"""
ONLINE -- 1. SIMULATE PRODUCTION TRAFFIC (logging)
==================================================

Online eval ka pehla qadam: production ma har conversation LOG karna.
Asli app nahi ha, isliye "fake users" bana kar traffic chalate hain aur wahi log
karte hain jo production ma karte:

    query, answer, contexts             -- baad ma COMPUTED signals (judge) ke liye
    latency_s, error                    -- CAPTURED signals (seedha store, kuch calculate nahi)
    feedback (thumbs up/down/none)      -- CAPTURED signal (user ne diya)
    abstained                           -- bot ne "I don't have enough information" bola?

Online ma golden answer NAHI hota -- users kuch bhi pooch sakte hain. Isliye traffic ma
sirf course sawal nahi, typos/Roman Urdu, off-topic aur tricky sawal bhi hain.

Feedback simulate: abstain ya off-topic pe thumbs down ka chance zyada (asli users jaisa).

Run:  python -m evals.07_online.simulate_traffic --n 20
Log:  online/logs/traffic.jsonl   (har line = ek conversation, append hota ha)
"""

import argparse
import json
import os
import random
import time
import uuid
from datetime import datetime

from dotenv import load_dotenv

from src.rag_pipeline import RagPipeline

load_dotenv()

LOG_PATH = "online/logs/traffic.jsonl"
ABSTAIN_TEXT = "I don't have enough information in the course material"

# real users ka mix -- koi golden answer nahi
USER_QUERIES = [
    # normal course sawal
    "what is online eval and how is it different from offline eval?",
    "faithfulness vs groundedness kya hota hai?",
    "why can't we just use benchmarks to pick a model?",
    "what is the rag triad?",
    "how does stratified sampling work in online evaluation?",
    "what is benchmark saturation?",
    "explain llm as a judge simply",
    "what are captured and computed signals?",
    "what does recall at k measure?",
    "why is vibe testing not enough?",
    # typos / Roman Urdu / short
    "drift kia hota hai deployment k baad",
    "mmlu pro vs mmlu difference??",
    "golden dataset kyun chahiye",
    "ref based vs ref free eval",
    # off-topic / out of knowledge base
    "what is the best laptop for machine learning?",
    "how do i fine tune llama 3 with lora?",
    "which vector database is fastest?",
    # tricky
    "is a faithful answer always a correct answer?",
    "can you give me the full transcript of session 3?",
    "what did the instructor say about air canada?",
]


def simulate_feedback(answer: str, off_topic_like: bool, rng: random.Random) -> str:
    abstained = ABSTAIN_TEXT.lower() in answer.lower()
    if abstained or off_topic_like:
        p_down, p_up = 0.6, 0.1
    else:
        p_down, p_up = 0.1, 0.4
    r = rng.random()
    if r < p_down:
        return "down"
    if r < p_down + p_up:
        return "up"
    return "none"          # zyada tar users feedback dete hi nahi


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=20, help="kitni conversations")
    ap.add_argument("--seed", type=int, default=7)
    args = ap.parse_args()

    rng = random.Random(args.seed)
    rag = RagPipeline()
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)

    off_topic = set(USER_QUERIES[14:17])
    for i in range(args.n):
        query = rng.choice(USER_QUERIES)
        t0 = time.perf_counter()
        try:
            out = rag.invoke(query)
            answer, contexts, error = out["answer"], out["context"], ""
        except Exception as e:
            answer, contexts, error = "", [], f"{type(e).__name__}: {e}"
        latency = time.perf_counter() - t0

        record = {
            "conversation_id": str(uuid.uuid4())[:8],
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "query": query,
            "answer": answer,
            "contexts": contexts,
            "latency_s": round(latency, 2),
            "error": error,
            "abstained": ABSTAIN_TEXT.lower() in answer.lower(),
            "feedback": simulate_feedback(answer, query in off_topic, rng) if not error else "none",
        }
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        print(f"[{i + 1}/{args.n}] {latency:5.1f}s  fb={record['feedback']:<4}  {query[:60]}")

    print(f"\nLogged {args.n} conversations -> {LOG_PATH}")


if __name__ == "__main__":
    main()
