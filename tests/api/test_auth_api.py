"""Auth API smoke test: signup → login → logout (POST preferred, GET fallback)."""

from tests.common import find_api_route


def _json(resp):
    return resp.get_json(silent=True) or {}


def test_signup_login_logout_flow(client, app):
    # Discover routes (supports slight naming differences)
    signup_url = find_api_route(app, ["signup"], "POST") or find_api_route(app, ["users"], "POST")
    login_url = find_api_route(app, ["login"], "POST")
    logout_post = find_api_route(app, ["logout"], "POST")
    logout_get = find_api_route(app, ["logout"], "GET")

    assert signup_url and login_url, f"Missing signup/login: signup={signup_url}, login={login_url}"

    # --- signup ---
    r = client.post(signup_url, json={"username": "api_user1", "password": "pw"})
    assert r.status_code in (200, 201, 409), r.get_data(as_text=True)

    # --- login ---
    r = client.post(login_url, json={"username": "api_user1", "password": "pw"})
    assert r.status_code in (200, 201), r.get_data(as_text=True)
    assert isinstance(_json(r), dict)

    # --- logout (prefer POST; fall back to GET if that’s what exists) ---
    if logout_post:
        rr = client.post(logout_post)
        assert rr.status_code in (200, 204, 302), rr.get_data(as_text=True)
    elif logout_get:
        rr = client.get(logout_get)
        assert rr.status_code in (200, 204, 302), rr.get_data(as_text=True)