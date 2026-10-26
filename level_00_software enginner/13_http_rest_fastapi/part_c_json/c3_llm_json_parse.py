"""
C.3 LLM ke JSON output ko parse + validate karna (Pydantic)
==========================================================
Server ki zaroorat NAHI.
    python -m part_c_json.c3_llm_json_parse

Theory: part_c_json/NOTES.md (C.3)
"""
import re
from typing import Literal

from pydantic import BaseModel, Field, ValidationError


class Intent(BaseModel):
    """Jo shape hum LLM se chahte hain."""
    intent: Literal["order_status", "faq", "complaint", "other"]
    order_id: str | None = Field(default=None, pattern=r"^\d{4}$")
    confidence: float = Field(ge=0, le=1)


def parse_llm_json(text: str) -> Intent | None:
    # 1. ```json ... ``` code fence ho to andar ka hissa lo
    match = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    candidate = match.group(1) if match else text
    # 2. Pehle { se aakhri } tak (aage peeche ka faalto text hata do)
    start, end = candidate.find("{"), candidate.rfind("}")
    if start == -1 or end == -1:
        print("   [!] JSON mila hi nahi")
        return None
    # 3. Parse + validate ek saath
    try:
        return Intent.model_validate_json(candidate[start:end + 1])
    except ValidationError as e:
        print("   [!] Validation fail:", e.errors()[0]["loc"], e.errors()[0]["msg"])
        return None


llm_outputs = [
    '{"intent": "order_status", "order_id": "1042", "confidence": 0.93}',
    'Sure! Here is the JSON:\n```json\n{"intent": "faq", "confidence": 0.8}\n```\nHope it helps!',
    '{"intent": "refund", "confidence": 0.7}',                          # ghalat intent
    '{"intent": "order_status", "order_id": "10", "confidence": 1.4}',  # ghalat id + confidence
    "Maaf kijiye, main samajh nahi saka.",                              # JSON hi nahi
]

for out in llm_outputs:
    print("LLM:", out.replace("\n", " ")[:60])
    print("   ->", parse_llm_json(out))

# ---- Khud try karein ----
# Intent mein ek naya field jorein: language: Literal["urdu", "english"]
# aur dekhein purane outputs ab kyun fail hote hain (aur default dene se kya hota hai)
