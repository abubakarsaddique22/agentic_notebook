"""
================================================================================
 M8.7  RED TEAMING  --  SAB KUCH EK FILE MEIN
================================================================================

Yeh file 2 purani files (attack_suite.py + deepteam_redteam.py) ko ek jagah jama
kar deti hai, isi tarteeb mein:

    HISSA 1  -> ATTACK      : ATTACKS list (M8.2 ki 6 attacks) jo dono agents par
                              chalti hain  [source of truth: m8_2/attacks.py]
    HISSA 2  -> PROTECTION  : yahan koi nayi defence NAHI -- hum SECURE agent
                              (m8_9, jo M8.3+M8.4+M8.5+M8.6 ka jama hai) ko TEST
                              karte hain. Insecure agent (app/) baseline hai.
    HISSA 3  -> RUN         : har attack insecure vs secure par chala kar ASR
                              (attack success rate) ka table + JSON report;
                              plus optional DeepTeam (--deepteam)

ASAL NUKTA (roadmap): "attack success rate track karo" + "har kamyab attack ko
permanent regression test bana do". ASR jitna kam, utna behtar.

`app/` ko haath nahi lagaya. Windows Chroma file-lock se bachne ke liye ismein
bhi _reindex_safe() hai (wahi jo m8_2/all_in_one.py mein).

--------------------------------------------------------------------------------
 CHALANA (Windows PowerShell) -- yeh commands AAP apne terminal mein chalayein:
--------------------------------------------------------------------------------
    cd C:\\Users\\abubakar\\Desktop\\security
    .venv\\Scripts\\activate
    python -m app.knowledge_base                                  # index pehle

    python -m m8_7_red_teaming.all_in_one --no-model-guard        # tez (Ollama kam)
    python -m m8_7_red_teaming.all_in_one                         # Ollama moderation ke saath

    # optional DeepTeam (khud attacks banata hai):
    #   pip install deepteam
    #   deepeval set-ollama --model gpt-oss:20b-cloud
    python -m m8_7_red_teaming.all_in_one --deepteam
================================================================================
"""
from __future__ import annotations

import argparse
import gc
import json
import shutil
import time
from datetime import datetime, timezone

from app.agent import build_agent, tool_calls, message_text, run_turn
from app.config import OUTPUT_DIR, CHROMA_DIR
from app.knowledge_base import build_index, DOCS_DIR, get_store

# ---- HISSA 1 ka source: ATTACKS list (M8.2 mein data ki tarah likhi hui) -------
from m8_2_prompt_injection.attacks import ATTACKS

# ---- HISSA 2: jise test karna hai -- SECURE agent (M8.9 = sab defences ka jama) -
from m8_9_capstone.secure_agent import build_secure_agent, secure_turn

REPORT = OUTPUT_DIR / "redteam_report.json"


# =============================================================================
#  HISSA 1 : ATTACK
# =============================================================================
# ATTACKS upar import ho chuki (m8_2/attacks.py). Woh 6 hain: S1 (BOLA order),
# S3 (system prompt leak), S2 (bara refund), S5 (poisoned doc exfil),
# S6 (read-then-exfil), S4 (staff notes leak). Har ek ka apna succeeded() check.
#
# Yaad rahe: S1/S2 ka check sirf dekhta hai ke tool CALL hua, result nahi. Is liye
# secure agent par bhi yeh "HIT" dikha sakte hain chahe tool ne kaam mana kar diya ho.


# =============================================================================
#  HISSA 2 : (jise test karte hain) -- secure vs insecure agent chalane ke helpers
# =============================================================================

def _reindex_safe() -> None:
    """Windows-safe reindex (WinError 32 file-lock fix) -- wahi jo m8_2 mein.
    Chroma ka khula handle chhoro, folder retry se mitao, phir fresh index."""
    get_store.cache_clear()
    gc.collect()
    for _ in range(5):
        if not CHROMA_DIR.exists():
            break
        try:
            shutil.rmtree(CHROMA_DIR)
            break
        except PermissionError:
            gc.collect()
            time.sleep(0.5)
    build_index(reset=False)


def _run_insecure(agent, turns):
    """Insecure agent (app/) par saare turns -> tool calls + aakhri jawab."""
    history, calls, text = [], [], ""
    for t in turns:
        res = run_turn(agent, t, history)
        calls += tool_calls(res)
        text = message_text(res["messages"][-1])
        history = res["messages"]
    return calls, text


def _run_secure(agent, turns, use_model_guard):
    """Secure agent (m8_9) par wahi. Block ho to history nahi badalti."""
    history, calls, text = [], [], ""
    for t in turns:
        res = secure_turn(agent, t, history, use_model_guard=use_model_guard)
        calls += res.get("_tool_calls", [])
        text = message_text(res["messages"][-1])
        history = res.get("messages", []) if not res.get("blocked") else history
    return calls, text


# =============================================================================
#  HISSA 3 : RUN  (ASR naapo -- insecure vs secure -- aur report)
# =============================================================================

def evaluate(target: str, use_model_guard: bool = True) -> dict:
    """Ek target (insecure/secure) par saare attacks chala kar ASR nikaalo."""
    build = build_secure_agent if target == "secure" else build_agent
    results = []
    succeeded = 0
    for atk in ATTACKS:
        # indirect attack (S5) ko pehle apna zehreela doc index mein chahiye
        if atk.poison_doc:
            (DOCS_DIR / atk.poison_doc[0]).write_text(atk.poison_doc[1], encoding="utf-8")
            _reindex_safe()
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
                _reindex_safe()
        succeeded += int(hit)
        results.append({"id": atk.id, "kind": atk.kind, "succeeded": hit})

    return {
        "target": target,
        "total": len(ATTACKS),
        "succeeded": succeeded,
        "attack_success_rate": round(succeeded / len(ATTACKS), 3),
        "results": results,
    }


def run_deepteam() -> None:
    """Optional: DeepTeam (named framework) khud attacks banata hai aur secure
    agent ko black-box ki tarah hamla karta hai. Ollama par chalta hai."""
    def model_callback(user_input: str) -> str:
        agent = build_secure_agent()
        # andar ka model-guard off (bhaari Llama Guard nest na ho); rails + code defences chalte hain
        res = secure_turn(agent, user_input, use_model_guard=False)
        return message_text(res["messages"][-1])

    try:
        from deepteam import red_team
        from deepteam.vulnerabilities import PromptLeakage, PIILeakage
        from deepteam.attacks.single_turn import PromptInjection
    except ImportError:
        print("deepteam not installed. Run: pip install deepteam")
        print("Then: deepeval set-ollama --model gpt-oss:20b-cloud")
        return

    risk = red_team(
        model_callback=model_callback,
        vulnerabilities=[PromptLeakage(), PIILeakage()],
        attacks=[PromptInjection()],
    )
    print(risk)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-model-guard", action="store_true")
    parser.add_argument("--deepteam", action="store_true", help="DeepTeam red-team chalao (optional)")
    args = parser.parse_args()

    if args.deepteam:
        run_deepteam()
        return

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
    print("\nYaad rahe: S1/S2 secure par bhi 'HIT' dikha sakte hain -- check sirf tool")
    print("CALL dekhta hai, result nahi (secure agent ne asal mein mana kar diya hota hai).\n")


if __name__ == "__main__":
    main()
