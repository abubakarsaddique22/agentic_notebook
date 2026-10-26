"""B.5 Basic assert + parametrize."""
import pytest

from bot.models import Message


def test_new_conversation_is_empty(convo):
    assert convo.messages == []


def test_add_message(convo):
    convo.add("user", "Salam")
    assert len(convo.messages) == 1
    assert convo.messages[0] == Message("user", "Salam")


def test_history_is_trimmed(convo):
    for i in range(10):
        convo.add("user", f"msg {i}")
    assert len(convo.messages) == 4                 # max_history=4 (conftest)
    assert convo.messages[0].content == "msg 6"     # purane kat gaye


def test_api_format_starts_with_system(convo):
    convo.add("user", "Hello")
    api = convo.to_api_format()
    assert api[0]["role"] == "system"
    assert api[-1] == {"role": "user", "content": "Hello"}


@pytest.mark.parametrize("role", ["user", "assistant"])
def test_message_to_api(role):
    assert Message(role, "hi").to_api() == {"role": role, "content": "hi"}
