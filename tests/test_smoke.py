def test_health_endpoint_requires_auth(client, contractor_user):
    resp = client.get("/health/")
    assert resp.status_code in {401, 403}

    client.force_login(contractor_user)
    resp = client.get("/health/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in {"ok", "error"}
    assert set(data.keys()) >= {"db", "redis", "celery", "status"}

