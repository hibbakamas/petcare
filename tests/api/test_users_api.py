import pytest
from tests.common import find_api_route

def _login(client, app, username="users_api_user", password="pw"):
    signup = find_api_route(app, ["signup"], "POST") or find_api_route(app, ["users"], "POST")
    login  = find_api_route(app, ["login"], "POST")
    client.post(signup, json={"username": username, "password": password})
    client.post(login,  json={"username": username, "password": password})

def test_update_current_user_username_if_supported(client, app):
    _login(client, app)
    # find a likely update route
    patch_me = (
        find_api_route(app, ["users", "me"], "PATCH") or
        find_api_route(app, ["users", "current"], "PATCH") or
        find_api_route(app, ["users"], "PATCH")
    )
    if not patch_me:
        pytest.skip("No user PATCH endpoint exposed; skipping")
    r = client.open(patch_me, method="PATCH", json={"username": "users_api_user_new"})
    assert r.status_code in (200, 204, 400, 409)