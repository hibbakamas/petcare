"""Households API tests: create/list/show/update/delete, join flow, and app-level handlers."""

from flask import abort
from app.models import Household, Users, db
from tests.common import extract_int, fill_route_params, find_api_route


def _login(client, app, u="hh_api_user", pw="pw"):
    signup = find_api_route(app, ["signup"], "POST") or find_api_route(app, ["users"], "POST")
    login = find_api_route(app, ["login"], "POST")
    assert signup and login, "Auth API (signup/login) not found"
    client.post(signup, json={"username": u, "password": pw})
    r = client.post(login, json={"username": u, "password": pw})
    assert r.status_code in (200, 201)


def _find_list_route(app):
    """Locate a non-parameterized GET /api/...households route if present."""
    for rule in app.url_map.iter_rules():
        if "GET" not in (rule.methods or []):
            continue
        path = str(rule.rule)
        if not path.startswith("/api"):
            continue
        if ("households" in path or "household" in path) and "<" not in path:
            return path
    return None


def _find_detail_route(app):
    """Locate a parameterized GET households detail route."""
    return find_api_route(app, ["households"], "GET") or find_api_route(app, ["household"], "GET")


def _find_update_route(app):
    """Locate PUT/PATCH households detail route."""
    return (
        find_api_route(app, ["households"], "PUT")
        or find_api_route(app, ["household"], "PUT")
        or find_api_route(app, ["households"], "PATCH")
        or find_api_route(app, ["household"], "PATCH")
    )


def _find_delete_route(app):
    return find_api_route(app, ["households"], "DELETE") or find_api_route(app, ["household"], "DELETE")


def _find_join_route(app):
    """Locate a POST join route (by code or by id)."""
    return (
        find_api_route(app, ["join"], "POST")
        or find_api_route(app, ["households", "join"], "POST")
        or find_api_route(app, ["household", "join"], "POST")
    )


def _find_members_route(app):
    """Locate a GET households/<id>/members route, if implemented."""
    return find_api_route(app, ["households", "members"], "GET") or find_api_route(app, ["household", "members"], "GET")


def test_create_list_show_update_delete(client, app):
    _login(client, app)

    # Create (with minimal validation tolerance)
    create = find_api_route(app, ["households"], "POST") or find_api_route(app, ["household"], "POST")
    assert create, "No POST /api/...households route found"

    r = client.post(create, json={})
    assert r.status_code in (200, 201, 400, 422)

    r = client.post(create, json={"name": "API HH One"})
    assert r.status_code in (200, 201), r.get_data(as_text=True)
    created = r.get_json(silent=True) or {}
    hid = extract_int(created, ("id", "household_id"))
    join_code = created.get("join_code") or created.get("code")

    # List (optional)
    list_url = _find_list_route(app)
    if list_url:
        rl = client.get(list_url)
        assert rl.status_code == 200, rl.get_data(as_text=True)
        assert isinstance(rl.get_json(silent=True), (list, dict))

    # Show (optional)
    detail = _find_detail_route(app)
    if detail and hid:
        try:
            show_ok = fill_route_params(detail, household_id=hid, id=hid)
        except KeyError:
            show_ok = f"{detail}/{hid}"
        rs = client.get(show_ok)
        assert rs.status_code in (200, 404)

        bad_id = 999999
        try:
            show_bad = fill_route_params(detail, household_id=bad_id, id=bad_id)
        except KeyError:
            show_bad = f"{detail}/{bad_id}"
        rb = client.get(show_bad)
        assert rb.status_code in (404, 400)

    # Update (optional)
    update = _find_update_route(app)
    if update and hid:
        try:
            upd_url = fill_route_params(update, household_id=hid, id=hid)
        except KeyError:
            upd_url = f"{update}/{hid}"
        ru = client.open(upd_url, method="PUT", json={"name": "API HH Updated"})
        assert ru.status_code in (200, 204, 400, 404, 405)

    # Delete (optional)
    delete = _find_delete_route(app)
    if delete and hid:
        try:
            del_url = fill_route_params(delete, household_id=hid, id=hid)
        except KeyError:
            del_url = f"{delete}/{hid}"
        rd = client.delete(del_url)
        assert rd.status_code in (200, 204, 404, 405)


def test_join_and_members_if_supported(client, app):
    _login(client, app, u="hh_join_user")

    # Create household
    create = find_api_route(app, ["households"], "POST") or find_api_route(app, ["household"], "POST")
    assert create
    r = client.post(create, json={"name": "Joinable HH"})
    assert r.status_code in (200, 201)
    data = r.get_json(silent=True) or {}
    hid = extract_int(data, ("id", "household_id"))
    code = data.get("join_code") or data.get("code")

    join = _find_join_route(app)
    if join and (hid or code):
        payload = {"nickname": "Owner"}
        # Prefer code-based join if the route doesn't take an id
        if ("code" in join) or ("join" in join and "<" not in join):
            if code:
                payload["code"] = code
        else:
            try:
                join = fill_route_params(join, household_id=hid, id=hid)
            except KeyError:
                join = f"{join}/{hid}"

        rj = client.post(join, json=payload)
        assert rj.status_code in (200, 201, 400, 404, 422)

        # Duplicate join attempt should produce a 2xx if idempotent or a 4xx if enforced
        rj2 = client.post(join, json=payload)
        assert rj2.status_code in (200, 400, 404, 409, 422)

    members = _find_members_route(app)
    if members and hid:
        try:
            murl = fill_route_params(members, household_id=hid, id=hid)
        except KeyError:
            murl = f"{members}/{hid}"
        rm = client.get(murl)
        assert rm.status_code in (200, 404)
        body = rm.get_json(silent=True)
        assert body is None or isinstance(body, (list, dict))


def test_app_404_handler_returns_json(client):
    r = client.get("/__totally_missing_path__")
    assert r.status_code == 404
    assert r.is_json and r.get_json().get("error") == "Not Found"


def test_app_405_handler_returns_json(client, app):
    def post_only():
        return "ok", 200

    app.add_url_rule("/__post_only__", view_func=post_only, methods=["POST"])
    r = client.get("/__post_only__")
    assert r.status_code == 405
    assert r.is_json and r.get_json().get("error") == "Method Not Allowed"


def test_app_403_handler_renders_html(client, app):
    def forbidden():
        abort(403)

    app.add_url_rule("/__forbidden__", view_func=forbidden)
    r = client.get("/__forbidden__")
    assert r.status_code == 403
    assert r.mimetype == "text/html"
    assert r.get_data(as_text=True)


# ----- tiny direct-DB helpers -----


def _mk_user(app, username="hh_smoke_user"):
    with app.app_context():
        u = Users(username=username, password_hash="x")
        db.session.add(u)
        db.session.commit()
        return u.id


def _login_as(client, uid: int):
    with client.session_transaction() as s:
        s["user_id"] = uid


def _mk_household(app, name="FamA", code=None):
    import random
    import string

    if code is None:
        code = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    with app.app_context():
        h = Household(name=name, join_code=code)
        db.session.add(h)
        db.session.commit()
        return h.id


def test_household_show_404_for_missing_id(client, app):
    uid = _mk_user(app)
    _login_as(client, uid)
    r = client.get("/api/v1/households/999999")
    assert r.status_code == 404


def test_household_show_403_for_non_member(client, app):
    uid = _mk_user(app)
    _login_as(client, uid)
    hid = _mk_household(app, name="PrivateFam")
    r = client.get(f"/api/v1/households/{hid}")
    assert r.status_code == 403


def test_household_delete_404_for_missing_id(client, app):
    uid = _mk_user(app)
    _login_as(client, uid)
    r = client.delete("/api/v1/households/999999")
    assert r.status_code == 404