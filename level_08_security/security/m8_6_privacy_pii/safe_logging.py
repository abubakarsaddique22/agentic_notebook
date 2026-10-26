"""PII-free, secret-free structured logging (roadmap M8.6).

Every log line passes through PII redaction and a secret scan first, so traces,
logs and audit records never become a second copy of the sensitive data we are
trying to protect. This logger is what the secure agent (M8.9) writes through.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from app.config import OUTPUT_DIR
from m8_6_privacy_pii.pii import redact
from m8_6_privacy_pii.secrets_scan import scan

LOG_FILE = OUTPUT_DIR / "audit.jsonl"


def _clean(value):
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
    """Write one sanitised audit record and return it."""
    record = {"ts": datetime.now(timezone.utc).isoformat(), "event": event, **_clean(fields)}
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    return record


if __name__ == "__main__":
    rec = log_event(
        "tool_call",
        tool="get_order",
        result="Ali Raza, phone 0300-0000001, key gsk_secretsecretsecret123456",
    )
    print(json.dumps(rec, indent=2, ensure_ascii=False))
