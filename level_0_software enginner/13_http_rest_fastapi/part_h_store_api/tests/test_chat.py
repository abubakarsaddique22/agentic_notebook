def test_order_question_skips_llm(client, auth, fake_llm):
    r = client.post("/v1/chat", json={"message": "Mera order 1042 kahan hai?"}, headers=auth)
    assert r.status_code == 200
    assert r.json()["source"] == "order_lookup"
    assert "shipped" in r.json()["reply"]
    assert fake_llm.calls == []                       # LLM ka paisa bacha


def test_general_question_uses_llm(client, auth, fake_llm):
    r = client.post("/v1/chat", json={"message": "COD hai?"}, headers=auth)
    assert r.json() == {"reply": "fake jawab", "source": "llm"}
    assert fake_llm.calls == ["COD hai?"]


def test_empty_message_rejected(client, auth):
    r = client.post("/v1/chat", json={"message": ""}, headers=auth)
    assert r.status_code == 422
    assert r.json()["error"]["details"][0]["field"] == "message"


def test_stream(client, auth):
    with client.stream("POST", "/v1/chat/stream", json={"message": "hi"}, headers=auth) as r:
        lines = [l for l in r.iter_lines() if l.startswith("data: ")]
    assert lines[-1] == "data: [DONE]"
    assert len(lines) == 3
