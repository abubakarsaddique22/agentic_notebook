"""B.8 Mocking: LLM ko monkeypatch se fake se badalna.

SAB SE AHAM RULE: wahan patch karein jahan function USE hota hai.
main.py mein `from bot.llm import ask_llm` hai, is liye:
  OK:  monkeypatch.setattr("bot.main.ask_llm", fake)
  X :  monkeypatch.setattr("bot.llm.ask_llm", fake)   <- main phir bhi asli wala chalaye ga!
"""
from bot.main import handle_message


def test_general_message_uses_llm(monkeypatch, convo, config):
    calls = []

    def fake_llm(messages, cfg):
        calls.append(messages)                # record karo ke kya bheja gaya
        return "Fake jawab"

    monkeypatch.setattr("bot.main.ask_llm", fake_llm)   # jahan USE hota hai

    reply = handle_message(convo, "Salam", config)

    assert reply == "Fake jawab"
    assert len(calls) == 1
    assert calls[0][0]["role"] == "system"              # system prompt gaya
    assert calls[0][-1]["content"] == "Salam"           # user ka message gaya
    assert convo.messages[-1].content == "Fake jawab"   # history mein save hua


def test_order_message_uses_tool(monkeypatch, convo, config):
    monkeypatch.setattr("bot.main.ask_llm", lambda m, c: "LLM nahi chalna chahiye tha")
    reply = handle_message(convo, "Mera order 1042 kahan hai?", config)
    assert "TCS" in reply
