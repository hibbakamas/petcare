from tests.common import find_api_route

def test_signup_login_logout_flow(client, app):
    signup_url = find_api_route(app, ["signup"], "POST") or find_api_route(app, ["users"], "POST")
    login_url  = find_api_route(app, ["login"], "POST")
    logout_post = find_api_route(app, ["logout"], "POST")
    logout_get  = find_api_route(app, ["logout"], "GET")

    assert signup_url and login_url, f"Missing signup/login: signup={signup_url}, login={login_url}"

    # signup (201/200 ok; 409 ok if duplicate)
    r = client.post(signup_url, json={"username": "api_user1", "password": "pw"})
    assert r.status_code in (200, 201, 409), r.get_data(as_text=True)

    # login
    r = client.post(login_url, json={"username": "api_user1", "password": "pw"})
    assert r.status_code in (200, 201)
    assert isinstance(r.get_json(silent=True) or {}, dict)

    # logout (prefer POST; fallback GET)
    if logout_post:
        rr = client.post(logout_post)
        assert rr.status_code in (200, 204, 302)
    elif logout_get:
        rr = client.get(logout_get)
        assert rr.status_code in (200, 204, 302)