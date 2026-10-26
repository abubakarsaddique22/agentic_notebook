"""Live regression tests: every known attack must FAIL against the secure agent.

These call the real model, so they are slow and need GROQ_API_KEY + the index
built. They are marked 'live' so you can skip them in quick runs:

    pytest tests/security -v -m "not live"      # fast, offline only
    pytest tests/security -v                     # everything (needs model)

Rule of the module: a vulnerability, once found, becomes a permanent test.
Any attack that still succeeds here is a real open bug to fix.
"""
import pytest

from app.knowledge_base import build_index, DOCS_DIR, CHROMA_DIR
from app.agent import message_text, tool_calls
from m8_2_prompt_injection.attacks import ATTACKS
from m8_9_capstone.secure_agent import build_secure_agent, secure_turn

pytestmark = pytest.mark.live


@pytest.fixture(scope="module", autouse=True)
def ensure_index():
    if not CHROMA_DIR.exists():
        build_index(reset=True)


@pytest.fixture(scope="module")
def agent():
    return build_secure_agent()


@pytest.mark.parametrize("atk", ATTACKS, ids=[a.id for a in ATTACKS])
def test_attack_is_blocked(agent, atk):
    # set up poisoned doc for indirect attacks
    if atk.poison_doc:
        (DOCS_DIR / atk.poison_doc[0]).write_text(atk.poison_doc[1], encoding="utf-8")
        build_index(reset=True)
    try:
        history, calls, text = [], [], ""
        for turn in atk.turns:
            res = secure_turn(agent, turn, history, use_model_guard=False)
            calls += res.get("_tool_calls", [])
            text = message_text(res["messages"][-1])
            history = res.get("messages", []) if not res.get("blocked") else history
        assert not atk.succeeded(calls, text), (
            f"{atk.id} STILL SUCCEEDS against the secure agent - open vulnerability"
        )
    finally:
        if atk.poison_doc:
            (DOCS_DIR / atk.poison_doc[0]).unlink(missing_ok=True)
            build_index(reset=True)
