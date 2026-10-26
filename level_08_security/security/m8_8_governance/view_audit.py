"""Summarise the audit log (M8.8 auditability).

Reads outputs/audit.jsonl (written by safe_logging.log_event) and prints counts
by event type, plus the blocked events. Shows that every action and every block
is on record.

    python -m m8_8_governance.view_audit
"""
from __future__ import annotations

import json
from collections import Counter

from m8_6_privacy_pii.safe_logging import LOG_FILE


def main() -> None:
    if not LOG_FILE.exists():
        print("No audit log yet. Run the secure agent first.")
        return
    events = [json.loads(line) for line in LOG_FILE.read_text(encoding="utf-8").splitlines() if line.strip()]
    counts = Counter(e["event"] for e in events)

    print(f"Audit log: {LOG_FILE}  ({len(events)} events)\n")
    for event, n in counts.most_common():
        print(f"  {event:20} {n}")

    blocks = [e for e in events if e["event"].endswith("_blocked")]
    if blocks:
        print("\nBlocked events:")
        for e in blocks[-10:]:
            print(f"  {e['ts']}  {e['event']}  reasons={e.get('reasons')}")


if __name__ == "__main__":
    main()
