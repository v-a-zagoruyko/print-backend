def test_me_requires_auth(client):
    resp = client.get("/api/v1/system/me/")
    assert resp.status_code in {401, 403}


def test_me_returns_user_and_groups(client, print_operator_user):
    client.force_login(print_operator_user)
    resp = client.get("/api/v1/system/me/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["username"] == "print_operator"
    assert data["is_staff"] is False
    assert data["is_superuser"] is False
    assert "Печатник" in data["groups"]


def test_me_returns_company_name_from_base_info(client, print_operator_user):
    from main.models import BaseInfo

    info = BaseInfo.get_solo()
    info.name = "My Company"
    info.save()

    client.force_login(print_operator_user)
    resp = client.get("/api/v1/system/me/")
    assert resp.status_code == 200
    assert resp.json()["company_name"] == "My Company"
