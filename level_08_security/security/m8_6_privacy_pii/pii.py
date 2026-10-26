"""PII detection and redaction with Microsoft Presidio (roadmap M8.6).

Presidio runs fully locally (spaCy NER + regex recognizers), so no data leaves
the machine - important because the Groq free tier has no privacy SLA.

We add Pakistan-specific recognizers (mobile numbers, CNIC) because Presidio's
defaults are US-centric.

Setup:
    pip install presidio-analyzer presidio-anonymizer spacy
    python -m spacy download en_core_web_lg
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache


@dataclass
class Redaction:
    text: str
    found: list[str]   # entity types that were redacted


@lru_cache(maxsize=1)
def _engines():
    # AnalyzerEngine: text mein PII DHOONDTA hai (naam, email, phone waghera) aur
    #                 batata hai kahan kahan mila.
    # PatternRecognizer: apna custom detector banane ke liye (jaise PK phone, CNIC)
    #                    jo Presidio ke default US-centric detectors mein nahi.
    # Pattern: ek regex + naam + confidence score, jo PatternRecognizer ko diya jata hai.
    from presidio_analyzer import AnalyzerEngine, Pattern, PatternRecognizer
    # AnonymizerEngine: jo PII Analyzer ne dhoonda, usay CHHUPATA/replace karta hai
    #                   (jaise "Ali" -> "<PERSON>").
    from presidio_anonymizer import AnonymizerEngine

    analyzer = AnalyzerEngine()

    # Pakistan mobile: 03XX-XXXXXXX or +92 3XX XXXXXXX
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


# Entities we care about in this app.
DEFAULT_ENTITIES = [
    "PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER", "LOCATION",
    "CREDIT_CARD", "IBAN_CODE", "PK_PHONE", "PK_CNIC",
]


def redact(text: str, entities: list[str] | None = None) -> Redaction:
    """Replace detected PII with <ENTITY> placeholders."""
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


if __name__ == "__main__":
    sample = ("Customer Ali Raza, email ali.raza@example.com, phone 0300-0000001, "
              "CNIC 35202-1234567-1, lives in Model Town Lahore.")
    out = redact(sample)
    print("Found:", out.found)
    print("Redacted:", out.text)
