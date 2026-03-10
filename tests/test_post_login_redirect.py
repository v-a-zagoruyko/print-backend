from urllib.parse import quote


def test_post_login_redirect_without_url_goes_to_admin(client, contractor_user):
    client.force_login(contractor_user)
    resp = client.get("/post_login_redirect/")
    assert resp.status_code == 302
    assert resp["Location"] == "/"


def test_post_login_redirect_forbidden_origin_goes_to_admin(client, contractor_user):
    client.force_login(contractor_user)
    dest = "https://evil.example/path"
    resp = client.get(f"/post_login_redirect/?url={quote(dest)}")
    assert resp.status_code == 302
    assert resp["Location"] == "/"


def test_post_login_redirect_allowed_origin_redirects(client, contractor_user, settings):
    client.force_login(contractor_user)
    allowed_origin = settings.CORS_ALLOWED_ORIGINS[0]
    dest = f"{allowed_origin}/some/path?x=1"
    resp = client.get(f"/post_login_redirect/?url={quote(dest)}")
    assert resp.status_code == 302
    assert resp["Location"] == dest

