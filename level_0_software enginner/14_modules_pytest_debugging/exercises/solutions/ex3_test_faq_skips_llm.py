"""SOLUTION 3 (part 2): neeche wala test tests/test_main.py ke AAKHIR mein jor dein
(handle_message wahan pehle se import hai)."""
from bot.main import handle_message


def test_faq_skips_llm(monkeypatch, convo, config):
    # Agar LLM chala to test fail
    def must_not_run(messages, cfg):
        raise AssertionError("FAQ wale sawal par LLM nahi chalna chahiye!")

    monkeypatch.setattr("bot.main.ask_llm", must_not_run)
    reply = handle_message(convo, "COD hai?", config)
    assert "Cash on Delivery" in reply
