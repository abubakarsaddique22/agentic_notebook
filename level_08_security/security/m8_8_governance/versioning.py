"""Stamp every run with versions so logs and approvals are auditable (M8.8).

Auditability = being able to say later exactly which prompt, model and defence
config produced a given decision. We hash the system prompt so a silent prompt
change is detectable.
"""
from __future__ import annotations

import hashlib

from app.config import GROQ_MODEL

PROMPT_VERSION = "secure-v1"
DEFENSE_CONFIG_VERSION = "m8-full-v1"


def prompt_fingerprint(system_prompt: str) -> str:
    return hashlib.sha256(system_prompt.encode("utf-8")).hexdigest()[:12]


def run_stamp(system_prompt: str) -> dict:
    return {
        "prompt_version": PROMPT_VERSION,
        "prompt_sha": prompt_fingerprint(system_prompt),
        "model": GROQ_MODEL,
        "defense_config": DEFENSE_CONFIG_VERSION,
    }


if __name__ == "__main__":
    from m8_9_capstone.secure_agent import SECURE_SYSTEM_PROMPT
    import json
    print(json.dumps(run_stamp(SECURE_SYSTEM_PROMPT), indent=2))
