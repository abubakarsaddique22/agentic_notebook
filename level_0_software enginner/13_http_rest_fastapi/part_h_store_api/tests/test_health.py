def test_health(client):
    r = client.get("/v1/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
    assert "x-request-id" in r.headers


def test_request_id_is_echoed(client):
    r = client.get("/v1/health", headers={"X-Request-ID": "abc123"})
    assert r.headers["x-request-id"] == "abc123"


def test_unknown_route_uses_error_format(client):
    r = client.get("/v1/nahi-hai")
    assert r.status_code == 404
    assert r.json()["error"]["code"] == 404
