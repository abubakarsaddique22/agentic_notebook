import pytest


def test_requires_api_key(client):
    r = client.get("/v1/orders/1042")
    assert r.status_code == 401
    assert r.headers["www-authenticate"] == "ApiKey"
    assert r.json()["error"]["message"].startswith("API key")


def test_wrong_api_key(client):
    assert client.get("/v1/orders/1042", headers={"X-API-Key": "chori"}).status_code == 401


def test_get_order(client, auth):
    r = client.get("/v1/orders/1042", headers=auth)
    assert r.status_code == 200
    assert r.json() == {"order_id": "1042", "status": "shipped", "total_pkr": 4700, "courier": "TCS"}


def test_order_not_found(client, auth):
    r = client.get("/v1/orders/9999", headers=auth)
    assert r.status_code == 404
    assert "9999" in r.json()["error"]["message"]


@pytest.mark.parametrize("bad_id", ["12", "abcd", "12345"])
def test_invalid_order_id_format(client, auth, bad_id):
    r = client.get(f"/v1/orders/{bad_id}", headers=auth)
    assert r.status_code == 422
    assert r.json()["error"]["details"][0]["field"] == "order_id"


def test_list_filter_and_pagination(client, auth):
    r = client.get("/v1/orders", params={"limit": 2}, headers=auth)
    body = r.json()
    assert len(body["items"]) == 2 and body["total"] == 3
    r = client.get("/v1/orders", params={"status": "pending"}, headers=auth)
    assert [o["order_id"] for o in r.json()["items"]] == ["1043"]


def test_list_rejects_bad_status(client, auth):
    assert client.get("/v1/orders", params={"status": "lost"}, headers=auth).status_code == 422
