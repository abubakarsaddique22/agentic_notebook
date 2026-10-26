"""Scan text/code for leaked secrets before it is logged, stored or sent.

Two layers, same as guardrails:
  1. fast regex for the secret shapes we care about (API keys, tokens)
  2. detect-secrets (Yelp) as a broader plugin-based scanner

Use `scan()` on anything about to leave the trust boundary (logs, emails,
eval datasets). A secret must never land in a prompt, log or trace.

    pip install detect-secrets
"""
from __future__ import annotations

import re

_PATTERNS = {
    "groq_key": re.compile(r"\bgsk_[A-Za-z0-9]{20,}\b"),
    "openai_key": re.compile(r"\bsk-[A-Za-z0-9]{20,}\b"),
    "aws_key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "bearer": re.compile(r"(?i)bearer\s+[A-Za-z0-9._\-]{20,}"),
    "password_kv": re.compile(r"(?i)(password|passwd|secret|token)\s*[:=]\s*\S+"),
}


def scan(text: str) -> list[str]:
    """Return a list of secret types found. Empty = clean."""
    hits = [name for name, rx in _PATTERNS.items() if rx.search(text)]

    try:  # broaden with detect-secrets if available
        # scan_line: detect-secrets (Yelp) ka function jo ek line mein chhupe
        #            secrets (keys/tokens) dhoondta hai, hamare regex se zyada qisam pakarta hai.
        from detect_secrets.core.scan import scan_line
        for line in text.splitlines():
            for secret in scan_line(line):
                hits.append(f"detect-secrets:{secret.type}")
    except Exception:
        pass

    return sorted(set(hits))


def has_secret(text: str) -> bool:
    return bool(scan(text))


if __name__ == "__main__":
    samples = [
        "normal support message",
        "my key is gsk_abcdefghij1234567890ABCDE",
        "password = hunter2supersecretvalue",
    ]
    for s in samples:
        print(f"{scan(s) or 'clean':40} | {s}")
