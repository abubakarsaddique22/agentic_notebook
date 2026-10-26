"""Our own red-team harness: run every M8.2 attack against insecure AND secure
agents and report the attack-success rate (ASR) for each.

This is the roadmap's "track attack-success rate" + "turn vulnerabilities into
regression tests" in action. It needs no extra install (unlike DeepTeam) and
uses the attacks we already wrote, so it runs anywhere the app runs.

    python -m m8_7_red_teaming.attack_suite
    python -m m8_7_red_teaming.attack_suite --no-model-guard   # faster
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone

from app.agent import build_agent, tool_calls, message_text, run_turn
from app.config import OUTPUT_DIR
from app.knowledge_base import build_index, DOCS_DIR
from m8_2_prompt_injection.attacks import ATTACKS
from m8_9_capstone.secure_agent import build_secure_agent, secure_turn

REPORT = OUTPUT_DIR / "redteam_report.json"


def _run_insecure(agent, turns):
    history, calls, text = [], [], ""
    for t in turns:
        res = run_turn(agent, t, history)
        calls += tool_calls(res)
        text = message_text(res["messages"][-1])
        history = res["messages"]
    return calls, text


def _run_secure(agent, turns, use_model_guard):
    history, calls, text = [], [], ""
    for t in turns:
        res = secure_turn(agent, t, history, use_model_guard=use_model_guard)
        calls += res.get("_tool_calls", [])
        text = message_text(res["messages"][-1])
        # secure_turn returns real LC messages on success; keep history only then
        history = res.get("messages", []) if not res.get("blocked") else history
    return calls, text


def evaluate(target: str, use_model_guard: bool = True) -> dict:
    build = build_secure_agent if target == "secure" else build_agent
    results = []
    succeeded = 0
    for atk in ATTACKS:
        if atk.poison_doc:
            (DOCS_DIR / atk.poison_doc[0]).write_text(atk.poison_doc[1], encoding="utf-8")
            build_index(reset=True)
        try:
            agent = build()
            if target == "secure":
                calls, text = _run_secure(agent, atk.turns, use_model_guard)
            else:
                calls, text = _run_insecure(agent, atk.turns)
            hit = bool(atk.succeeded(calls, text))
        finally:
            if atk.poison_doc:
                (DOCS_DIR / atk.poison_doc[0]).unlink(missing_ok=True)
                build_index(reset=True)
        succeeded += int(hit)
        results.append({"id": atk.id, "kind": atk.kind, "succeeded": hit})

    return {
        "target": target,
        "total": len(ATTACKS),
        "succeeded": succeeded,
        "attack_success_rate": round(succeeded / len(ATTACKS), 3),
        "results": results,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-model-guard", action="store_true")
    args = parser.parse_args()
    use_guard = not args.no_model_guard

    print("Running red-team suite (this calls the model several times)...\n")
    insecure = evaluate("insecure")
    secure = evaluate("secure", use_model_guard=use_guard)

    report = {
        "generated": datetime.now(timezone.utc).isoformat(),
        "insecure": insecure,
        "secure": secure,
    }
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"{'attack':30} {'insecure':>10} {'secure':>10}")
    print("-" * 52)
    si = {r["id"]: r["succeeded"] for r in insecure["results"]}
    ss = {r["id"]: r["succeeded"] for r in secure["results"]}
    for atk in ATTACKS:
        print(f"{atk.id:30} {'HIT' if si[atk.id] else 'ok':>10} {'HIT' if ss[atk.id] else 'ok':>10}")
    print("-" * 52)
    print(f"{'ASR':30} {insecure['attack_success_rate']:>10} {secure['attack_success_rate']:>10}")
    print(f"\nFull report: {REPORT}")


if __name__ == "__main__":
    main()
