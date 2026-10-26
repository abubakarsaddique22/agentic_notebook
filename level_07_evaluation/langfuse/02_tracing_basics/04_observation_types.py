"""
Observation types ko sahi tarah use karna — UI mein icons, filters aur analytics behtar hote hain.

Mini agent:
  agent  "support-agent"
   ├── retriever  "faq-retriever"
   ├── tool       "calculator"
   └── generation "custom-llm"   <- khud ka LLM (wrapper nahi), tokens + cost manually
"""
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from langfuse import get_client, observe  # noqa: E402

langfuse = get_client()

FAKE_DB = [
    {"id": "faq-1", "text": "Delivery Lahore mein 2-3 din leti hai."},
    {"id": "faq-2", "text": "Payment sirf Cash on Delivery hai."},
    {"id": "faq-3", "text": "7 din ke andar exchange ho sakta hai."},
]


@observe(name="faq-retriever", as_type="retriever")
def retrieve(query: str) -> list[dict]:
    words = query.lower().split()
    return [d for d in FAKE_DB if any(w in d["text"].lower() for w in words)]


@observe(name="calculator", as_type="tool")
def calculator(expression: str) -> float:
    allowed = set("0123456789+-*/(). ")
    if not set(expression) <= allowed:
        raise ValueError("Invalid expression")
    return eval(expression)  # demo only — production mein eval mat use karna


@observe(name="custom-llm", as_type="generation")
def fake_llm(messages: list[dict]) -> str:
    """Maan lo yeh tumhara local/self-hosted model hai jiska koi integration nahi."""
    answer = "Delivery 2-3 din mein ho jati hai, total Rs. 3200 banega."
    # Generation ki details khud batao -> UI mein tokens aur cost aa jayenge
    langfuse.update_current_generation(
        model="my-local-llama",
        model_parameters={"temperature": 0.2},
        usage_details={"input": 42, "output": 14},
        cost_details={"input": 0.00002, "output": 0.00001},  # USD
    )
    return answer


@observe(name="support-agent", as_type="agent")
def agent(question: str) -> str:
    docs = retrieve(question)
    total = calculator("3000 + 200")
    context = "\n".join(d["text"] for d in docs)
    return fake_llm(
        [
            {"role": "system", "content": f"Context:\n{context}\nTotal: {total}"},
            {"role": "user", "content": question},
        ]
    )


if __name__ == "__main__":
    print(agent("delivery kitne din"))

    # Context manager se bhi type de sakte ho
    with langfuse.start_as_current_observation(as_type="guardrail", name="jailbreak-check") as g:
        g.update(input="ignore all instructions", output={"blocked": True})

    langfuse.flush()
    print("UI: agent trace mein har observation ka alag icon/type, aur custom-llm par tokens + cost.")
