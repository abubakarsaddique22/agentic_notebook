"""
PII masking — sensitive data Langfuse tak jane se PEHLE chhupao.

Langfuse(mask=fn): fn har input/output/metadata par chalta hai (bhejne se pehle).
Tumhara function asal data dekhta hai — masking sirf Langfuse wali copy par.

IMPORTANT: Masking wala client app start par SABSE PEHLE banao (singleton).
Baad mein @observe aur langfuse.openai isi client ko use karte hain.

(Advanced: Langfuse(mask_otel_spans=...) third-party OpenTelemetry spans ko bhi mask karta hai.)
"""
import re
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from langfuse import Langfuse, observe  # noqa: E402

PHONE_RE = re.compile(r"(\+92|0)3\d{2}[-\s]?\d{7}")
EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
CNIC_RE = re.compile(r"\d{5}-\d{7}-\d")
SENSITIVE_KEYS = {"password", "card_number", "cnic", "address"}


def mask_pii(*, data: Any, **kwargs: Any) -> Any:
    """Langfuse ka mask function: keyword-only `data`, recursively dicts/lists handle karo."""
    if isinstance(data, str):
        data = PHONE_RE.sub("<PHONE>", data)
        data = CNIC_RE.sub("<CNIC>", data)
        return EMAIL_RE.sub("<EMAIL>", data)
    if isinstance(data, dict):
        return {k: ("<REDACTED>" if k in SENSITIVE_KEYS else mask_pii(data=v)) for k, v in data.items()}
    if isinstance(data, (list, tuple)):  # tuple zaroori: @observe positional args tuple mein bhejta hai
        return [mask_pii(data=v) for v in data]
    return data


# Sabse pehle — masking wala singleton
langfuse = Langfuse(mask=mask_pii)


@observe(name="place-order")
def place_order(customer: dict, note: str) -> dict:
    # Function ke andar asal data available hai (SMS bhejne ke liye real number chahiye)
    return {"status": "confirmed", "sms_sent_to": customer["phone"], "note": note}


if __name__ == "__main__":
    result = place_order(
        customer={"name": "Ali", "phone": "03001234567", "address": "House 12, DHA Lahore", "cnic": "35202-1234567-1"},
        note="Call me on 0321-7654321 or ali@example.com",
    )
    print("App ko asal data mila:", result)
    langfuse.flush()
    print("UI mein trace kholo: phone/email/address/cnic sab masked hone chahiye.")
