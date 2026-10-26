"""Run every attack against either the insecure or the defended agent.

    python -m m8_2_prompt_injection.run_attacks --target insecure
    python -m m8_2_prompt_injection.run_attacks --target defended
    python -m m8_2_prompt_injection.run_attacks --target defended --kind indirect

Output per attack: SUCCESS (attack worked -> bad) or BLOCKED (defence held -> good),
plus the tool calls it made, so you can see exactly what happened.
"""
from __future__ import annotations

import argparse

from app.agent import build_agent, tool_calls, message_text, run_turn
from app.knowledge_base import build_index, DOCS_DIR
from m8_2_prompt_injection.attacks import by_kind
from m8_2_prompt_injection.defended_agent import build_defended_agent, run_turn_defended


def run_conversation(target: str, agent, turns: list[str]) -> tuple[list[dict], str]:
    """Play all turns, carrying history, and collect every tool call + the last reply."""
    history: list = []
    all_calls: list[dict] = []
    final_text = ""
    for turn in turns:
        if target == "defended":
            result = run_turn_defended(agent, turn, history)
        else:
            result = run_turn(agent, turn, history)
        all_calls += tool_calls(result)
        final_text = message_text(result["messages"][-1])
        history = result["messages"]
    return all_calls, final_text


def write_poison(filename: str, content: str) -> None:
    (DOCS_DIR / filename).write_text(content, encoding="utf-8")


def remove_poison(filename: str) -> None:
    (DOCS_DIR / filename).unlink(missing_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", choices=["insecure", "defended"], default="insecure")
    parser.add_argument("--kind", default=None, help="direct | indirect | exfiltration | jailbreak")
    args = parser.parse_args()

    attacks = by_kind(args.kind)
    build_fn = build_defended_agent if args.target == "defended" else build_agent

    print(f"\nTarget: {args.target} agent | attacks: {len(attacks)}\n" + "-" * 64)
    succeeded = 0
    for atk in attacks:
        # indirect attacks need their poisoned doc in the index first
        if atk.poison_doc:
            write_poison(*atk.poison_doc)
            build_index(reset=True)
        try:
            agent = build_fn()
            calls, final_text = run_conversation(args.target, agent, atk.turns)
            hit = atk.succeeded(calls, final_text)
        finally:
            if atk.poison_doc:
                remove_poison(atk.poison_doc[0])
                build_index(reset=True)

        succeeded += int(hit)
        verdict = "SUCCESS (bad)" if hit else "BLOCKED (good)"
        print(f"[{atk.kind:12}] {atk.id:28} -> {verdict}")
        for c in calls:
            print(f"                 tool: {c['name']}({c['args']})")

    print("-" * 64)
    print(f"{succeeded}/{len(attacks)} attacks succeeded against the {args.target} agent.")
    print("Lower is better. Remaining successes get fixed in M8.3-M8.6.\n")


if __name__ == "__main__":
    main()
