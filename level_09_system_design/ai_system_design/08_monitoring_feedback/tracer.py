"""
Module 8 · Minimal production tracer (SQLite)
=============================================

Har request ka EK trace record: input, output, VERSIONS, latency, tokens, cost, route,
degradation level, cache hit, retrieved chunk IDs, aur baad mein aane wala FEEDBACK.

Kyun khud ka chhota tracer?  Taake samajh aaye ke Langfuse / LangSmith / Phoenix andar se
kya store karte hain. Production mein inhi tools ko use karo (langfuse_tracing.py dekho).

Sab se important column: VERSIONS (app, prompt, model, retrieval config, kb).
Inke bina "kal se quality kyun giri?" ka jawab dena namumkin hai.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS traces (
    trace_id TEXT PRIMARY KEY,
    ts REAL, day INTEGER,
    tenant TEXT, user_hash TEXT, session_id TEXT,
    input TEXT, output TEXT,
    intent TEXT, route TEXT, level TEXT,
    app_version TEXT, prompt_version TEXT, model TEXT, served_by TEXT,
    retrieval_config TEXT, kb_version INTEGER,
    latency_ms REAL, ttft_ms REAL, tokens_in INTEGER, tokens_out INTEGER, cost_usd REAL,
    cache_hit TEXT, retrieved_ids TEXT, tool_calls TEXT, error TEXT
);
CREATE TABLE IF NOT EXISTS feedback (
    id TEXT PRIMARY KEY, trace_id TEXT, ts REAL,
    kind TEXT,          -- explicit | implicit
    signal TEXT,        -- thumbs | rephrase | asked_human | abandoned | resolved
    value REAL,         -- +1 / -1 / 0
    comment TEXT
);
CREATE INDEX IF NOT EXISTS idx_traces_day ON traces(day);
CREATE INDEX IF NOT EXISTS idx_feedback_trace ON feedback(trace_id);
"""


def hash_user(phone: str) -> str:
    """PII: raw phone number log mat karo. Hash (salt ke saath, production mein secret salt)."""
    return hashlib.sha256(f"demo-salt:{phone}".encode()).hexdigest()[:12]


@dataclass
class TraceRecord:
    input: str
    output: str = ""
    tenant: str = "default"
    user_hash: str = ""
    session_id: str = ""
    intent: str = ""
    route: str = ""
    level: str = "primary"
    app_version: str = ""
    prompt_version: str = ""
    model: str = ""
    served_by: str = ""
    retrieval_config: str = ""
    kb_version: int = 0
    latency_ms: float = 0.0
    ttft_ms: float = 0.0
    tokens_in: int = 0
    tokens_out: int = 0
    cost_usd: float = 0.0
    cache_hit: str = "none"
    retrieved_ids: list[str] = field(default_factory=list)
    tool_calls: list[str] = field(default_factory=list)
    error: str = ""
    trace_id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    ts: float = field(default_factory=time.time)
    day: int = 0


class Tracer:
    def __init__(self, path: str | Path) -> None:
        self.db = sqlite3.connect(str(path))
        self.db.executescript(SCHEMA)

    def log(self, rec: TraceRecord) -> str:
        d = asdict(rec)
        d["retrieved_ids"] = json.dumps(d["retrieved_ids"])
        d["tool_calls"] = json.dumps(d["tool_calls"])
        cols = ",".join(d)
        self.db.execute(f"INSERT INTO traces ({cols}) VALUES ({','.join('?' * len(d))})",
                        list(d.values()))
        return rec.trace_id

    def feedback(self, trace_id: str, kind: str, signal: str, value: float,
                 comment: str = "", ts: float | None = None) -> None:
        self.db.execute("INSERT INTO feedback VALUES (?,?,?,?,?,?,?)",
                        (uuid.uuid4().hex[:12], trace_id, ts or time.time(), kind, signal,
                         value, comment))

    def commit(self) -> None:
        self.db.commit()

    def query(self, sql: str, params: tuple = ()) -> list[tuple]:
        return self.db.execute(sql, params).fetchall()
