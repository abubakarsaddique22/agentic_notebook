"""
================================================================================
 M8.6  PRIVACY, PII & SECRETS  --  SAB KUCH EK FILE MEIN
================================================================================

Yeh file 3 purani files (pii.py + secrets_scan.py + safe_logging.py) ko ek jagah
jama kar deti hai, isi tarteeb mein:

    HISSA 1  -> ATTACK      : woh text jo leak nahi hona chahiye --
                              (a) PII (naam, email, phone, CNIC)
                              (b) secrets (API keys, passwords)
    HISSA 2  -> PROTECTION  : (a) redact  = Presidio se PII -> <ENTITY> (local, PK recognizers)
                              (b) scan     = regex + detect-secrets se keys/tokens pakarna
                              (c) log_event= log likhne se PEHLE redact + scan (saaf audit)
    HISSA 3  -> RUN         : sample text redact + secret scan + ek saaf audit line

ASAL NUKTA: logs/traces/audit sensitive data ki doosri copy na ban jayein. Har
log line pehle redact + secret-scan se guzarti hai. Presidio poora LOCAL chalta
hai (spaCy NER + regex), data machine se bahar nahi jata.

`app/` ko haath nahi lagaya (sirf OUTPUT_DIR import).

--------------------------------------------------------------------------------
 SETUP (sirf ek dafa, Windows PowerShell):
--------------------------------------------------------------------------------
    pip install presidio-analyzer presidio-anonymizer spacy detect-secrets
    python -m spacy download en_core_web_lg

 CHALANA:
    cd C:\\Users\\abubakar\\Desktop\\security
    .venv\\Scripts\\activate
    python -m m8_6_privacy_pii.all_in_one
================================================================================
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from functools import lru_cache

from app.config import OUTPUT_DIR


# =============================================================================
#  HISSA 1 : ATTACK  (jo text leak nahi hona chahiye)
# =============================================================================
#
# Yeh woh cheezein hain jo galti se log/trace/email mein ja kar leak ho sakti
# hain. HISSA 3 inhe protection se guzaar kar dikhata hai ke saaf ho jati hain.

PII_SAMPLE = ("Customer Ali Raza, email ali.raza@example.com, phone 0300-0000001, "
              "CNIC 35202-1234567-1, lives in Model Town Lahore.")

SECRET_SAMPLES = [
    ("normal support message", False),                         # saaf
    ("my key is gsk_abcdefghij1234567890ABCDE", True),         # Groq API key
    ("password = hunter2supersecretvalue", True),              # password
]

# Ek "tool result" jis mein PII + secret dono hain (audit line ban kar jayega):
DIRTY_TOOL_RESULT = "Ali Raza, phone 0300-0000001, key gsk_secretsecretsecret123456"


# =============================================================================
#  HISSA 2 : PROTECTION  (redact + scan + safe log)
# =============================================================================

# -----------------------------------------------------------------------------
#  (a) PII redaction -- Microsoft Presidio (local), + Pakistan recognizers
# -----------------------------------------------------------------------------
@dataclass
class Redaction:
    text: str
    found: list[str]   # jo entity types redact huay


@lru_cache(maxsize=1)
def _engines():
    # AnalyzerEngine: text mein PII DHOONDTA hai aur batata hai kahan mila.
    # PatternRecognizer + Pattern: apna custom detector (PK phone, CNIC) jo Presidio
    #   ke default US-centric detectors mein nahi.
    from presidio_analyzer import AnalyzerEngine, Pattern, PatternRecognizer
    # AnonymizerEngine: jo PII mila usay chhupata/replace karta hai ("Ali" -> "<PERSON>").
    from presidio_anonymizer import AnonymizerEngine

    analyzer = AnalyzerEngine()

    # Pakistan mobile: 03XX-XXXXXXX ya +92 3XX XXXXXXX
    pk_phone = PatternRecognizer(
        supported_entity="PK_PHONE",
        patterns=[Pattern("pk_mobile", r"(\+92[\s-]?|0)3\d{2}[\s-]?\d{7}", 0.8)],
    )
    # CNIC: 12345-1234567-1
    cnic = PatternRecognizer(
        supported_entity="PK_CNIC",
        patterns=[Pattern("cnic", r"\b\d{5}-\d{7}-\d\b", 0.9)],
    )
    analyzer.registry.add_recognizer(pk_phone)
    analyzer.registry.add_recognizer(cnic)
    return analyzer, AnonymizerEngine()


# Is app mein jin entities ki parwah hai.
DEFAULT_ENTITIES = [
    "PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER", "LOCATION",
    "CREDIT_CARD", "IBAN_CODE", "PK_PHONE", "PK_CNIC",
]


def redact(text: str, entities: list[str] | None = None) -> Redaction:
    """Mili hui PII ko <ENTITY> placeholders se replace karo.
    DHYAAN: Presidio install na ho to text waisa hi chhorta hai (PII leak!) ->
    is liye presidio + en_core_web_lg zaroor install karein."""
    try:
        analyzer, anonymizer = _engines()
    except ImportError:
        return Redaction(text=text, found=["[presidio-not-installed]"])

    results = analyzer.analyze(text=text, entities=entities or DEFAULT_ENTITIES, language="en")
    if not results:
        return Redaction(text=text, found=[])
    anonymized = anonymizer.anonymize(text=text, analyzer_results=results)
    found = sorted({r.entity_type for r in results})
    return Redaction(text=anonymized.text, found=found)


# -----------------------------------------------------------------------------
#  (b) secrets scan -- regex (fast) + detect-secrets (broader)
# -----------------------------------------------------------------------------
_PATTERNS = {
    "groq_key": re.compile(r"\bgsk_[A-Za-z0-9]{20,}\b"),
    "openai_key": re.compile(r"\bsk-[A-Za-z0-9]{20,}\b"),
    "aws_key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "bearer": re.compile(r"(?i)bearer\s+[A-Za-z0-9._\-]{20,}"),
    "password_kv": re.compile(r"(?i)(password|passwd|secret|token)\s*[:=]\s*\S+"),
}


def scan(text: str) -> list[str]:
    """Mile hue secret types ki list. Khaali = saaf."""
    hits = [name for name, rx in _PATTERNS.items() if rx.search(text)]

    try:  # detect-secrets ho to aur qisam pakarti hai
        from detect_secrets.core.scan import scan_line
        for line in text.splitlines():
            for secret in scan_line(line):
                hits.append(f"detect-secrets:{secret.type}")
    except Exception:
        pass

    return sorted(set(hits))


def has_secret(text: str) -> bool:
    return bool(scan(text))


# -----------------------------------------------------------------------------
#  (c) safe logging -- har log line redact + scan ke baad hi likhti hai
# -----------------------------------------------------------------------------
LOG_FILE = OUTPUT_DIR / "audit.jsonl"


def _clean(value):
    """string -> secret mile to poora text [REDACTED-SECRET], phir PII redact.
    dict/list -> andar har cheez par khud ko dobara chalao (recursion)."""
    if isinstance(value, str):
        text = value
        if scan(text):
            text = "[REDACTED-SECRET]"
        text = redact(text).text
        return text
    if isinstance(value, dict):
        return {k: _clean(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_clean(v) for v in value]
    return value


def log_event(event: str, **fields) -> dict:
    """Ek saaf audit record likho aur wapas karo."""
    record = {"ts": datetime.now(timezone.utc).isoformat(), "event": event, **_clean(fields)}
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    return record


# =============================================================================
#  HISSA 3 : RUN  (redact + scan + ek saaf audit line)
# =============================================================================

def main() -> None:
    print("\n[PII redaction] Presidio se PII chhupana:\n" + "-" * 70)
    out = redact(PII_SAMPLE)
    print(f"  input : {PII_SAMPLE}")
    print(f"  found : {out.found}")
    print(f"  output: {out.text}")
    if out.found == ["[presidio-not-installed]"]:
        print("  (!) Presidio install nahi -> PII redact NAHI hui. Setup commands upar dekhein.")

    print("\n[secrets scan] keys / passwords pakarna:\n" + "-" * 70)
    for text, should_hit in SECRET_SAMPLES:
        hits = scan(text)
        ok = "(OK)" if bool(hits) == should_hit else "(WRONG)"
        print(f"  {str(hits) or 'clean':40} {ok} | {text}")

    print("\n[safe logging] PII + secret wala tool-result audit line ban kar:\n" + "-" * 70)
    rec = log_event("tool_call", tool="get_order", result=DIRTY_TOOL_RESULT)
    print(f"  raw result : {DIRTY_TOOL_RESULT}")
    print(f"  audit line : {json.dumps(rec, ensure_ascii=False)}")
    print(f"  (likha gaya: {LOG_FILE})")

    print("\n" + "-" * 70)
    print("Secret mile to poora field [REDACTED-SECRET], phir PII placeholders.")
    print("Is tarah audit.jsonl kabhi sensitive data ki doosri copy nahi banti.\n")


if __name__ == "__main__":
    main()
