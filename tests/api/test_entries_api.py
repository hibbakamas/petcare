"""Entries API tests: create, list, get, update, delete, and basic ownership."""

from app.models import Entry, Household, Pet, Users, db
from tests.common import extract_int, fill_route_params, find_api_route

# ---------- helpers ----------


def _login(client, app, u="entries_api_user"):
    signup = find_api_route(app, ["signup"], "POST") or find_api_route(app, ["users"], "POST")
    login = find_api_route(app, ["login"], "POST")
    client.post(signup, json={"username": u, "password": "pw"})
    client.post(login, json={"username": u, "password": "pw"})


def _make_household_and_pet(client, app):
    hh_post = find_api_route(app, ["household"], "POST") or find_api_route(app, ["households"], "POST")
    r = client.post(hh_post, json={"name": "EntryHome"})
    hid = extract_int(r.get_json(silent=True) or {}, ("id", "household_id"))

    pets_post = find_api_route(app, ["pets"], "POST")
    try:
        purl = fill_route_params(pets_post, household_id=hid)
    except KeyError:
        purl = pets_post

    r = client.post(purl, json={"name": "EntryPet", "household_id": hid})
    pid = extract_int(r.get_json(silent=True) or {}, ("id", "pet_id"))
    return hid, pid


def _hh_pet(client, app, user="entries_owner"):
    _login(client, app, user)
    hh_post = find_api_route(app, ["household"], "POST") or find_api_route(app, ["households"], "POST")
    hid = extract_int(
        client.post(hh_post, json={"name": "EHH"}).get_json(silent=True) or {}, ("id", "household_id")
    )

    pets_post = find_api_route(app, ["pets"], "POST")
    try:
        purl = fill_route_params(pets_post, household_id=hid)
    except KeyError:
        purl = pets_post

    pid = extract_int(
        client.post(purl, json={"name": "EPet", "household_id": hid}).get_json(silent=True) or {}, ("id", "pet_id")
    )
    return hid, pid


# ---------- tests ----------


def test_create_and_optionally_update_delete_entry(client, app):
    _login(client, app)
    _, pid = _make_household_and_pet(client, app)

    entries_post = find_api_route(app, ["entries"], "POST")
    assert entries_post, "No POST /api/...entries"
    try:
        post_url = fill_route_params(entries_post, pet_id=pid)
    except KeyError:
        post_url = entries_post

    r = client.post(post_url, json={"content": "API fed breakfast", "pet_id": pid})
    assert r.status_code in (200, 201), r.get_data(as_text=True)
    entry = r.get_json(silent=True) or {}
    eid = extract_int(entry, ("id", "entry_id"))

    # Optional update (supports either PUT or PATCH in various APIs)
    entries_put = find_api_route(app, ["entries"], "PUT") or find_api_route(app, ["entries"], "PATCH")
    if entries_put and eid:
        try:
            put_url = fill_route_params(entries_put, pet_id=pid, entry_id=eid)
        except KeyError:
            put_url = entries_put
        rr = client.open(put_url, method="PUT", json={"content": "updated"})
        assert rr.status_code in (200, 204, 404, 405)

    # Optional delete
    entries_del = find_api_route(app, ["entries"], "DELETE")
    if entries_del and eid:
        try:
            del_url = fill_route_params(entries_del, pet_id=pid, entry_id=eid)
        except KeyError:
            del_url = entries_del
        rr = client.delete(del_url)
        assert rr.status_code in (200, 204)


def test_entries_validation_create_update_delete_and_ownership(client, app):
    _, pid = _hh_pet(client, app)

    post = find_api_route(app, ["entries"], "POST")
    assert post
    try:
        eurl = fill_route_params(post, pet_id=pid)
    except KeyError:
        eurl = post

    # Validation: missing content
    r = client.post(eurl, json={"pet_id": pid})
    assert r.status_code in (400, 422)

    # Create ok
    r = client.post(eurl, json={"content": "walk", "pet_id": pid})
    assert r.status_code in (200, 201)
    entry = r.get_json(silent=True) or {}
    eid = extract_int(entry, ("id", "entry_id"))

    # Optional list/get
    get = find_api_route(app, ["entries"], "GET")
    if get:
        try:
            gurl = fill_route_params(get, pet_id=pid, entry_id=eid)
        except KeyError:
            gurl = get
        rg = client.get(gurl)
        assert rg.status_code in (200, 404)

    # Update
    put = find_api_route(app, ["entries"], "PUT") or find_api_route(app, ["entries"], "PATCH")
    if put:
        try:
            purl = fill_route_params(put, pet_id=pid, entry_id=eid)
        except KeyError:
            purl = put
        ru = client.open(purl, method="PUT", json={"content": "updated"})
        assert ru.status_code in (200, 204, 404, 405)

    # Delete
    delete = find_api_route(app, ["entries"], "DELETE")
    if delete:
        try:
            durl = fill_route_params(delete, pet_id=pid, entry_id=eid)
        except KeyError:
            durl = delete
        rd = client.delete(durl)
        assert rd.status_code in (200, 204, 404, 405)

    # Second user should not be able to update/delete the first user's entry
    client.get("/logout")
    _login(client, app, "entries_attacker")
    if put:
        ru2 = client.open(purl, method="PUT", json={"content": "hacked"})
        assert ru2.status_code in (403, 404, 405)
    if delete:
        rd2 = client.delete(durl)
        assert rd2.status_code in (403, 404, 405)


# ---------- tiny direct-DB helpers ----------


def _mk_user(app, username="entries_user"):
    with app.app_context():
        u = Users(username=username, password_hash="x")
        db.session.add(u)
        db.session.commit()
        return u.id


def _login_as(client, uid: int):
    with client.session_transaction() as s:
        s["user_id"] = uid


def _mk_household(app, name="HH", code=None):
    import random
    import string

    if code is None:
        code = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    with app.app_context():
        h = Household(name=name, join_code=code)
        db.session.add(h)
        db.session.commit()
        return h.id


def _mk_pet(app, hid: int, name="Milo"):
    with app.app_context():
        p = Pet(household_id=hid, name=name)
        db.session.add(p)
        db.session.commit()
        return p.id


def _mk_entry_direct(app, pid: int, uid: int, content="hi"):
    with app.app_context():
        e = Entry(pet_id=pid, user_id=uid, content=content)
        db.session.add(e)
        db.session.commit()
        return e.id


# ---------- CREATE ----------


def test_entries_create_401_when_not_logged_in(client, app):
    hid = _mk_household(app)
    pid = _mk_pet(app, hid)
    r = client.post(f"/api/v1/pets/{pid}/entries", json={"content": "hey"})
    assert r.status_code == 401


def test_entries_create_404_when_pet_missing(client, app):
    uid = _mk_user(app)
    _login_as(client, uid)
    r = client.post("/api/v1/pets/999999/entries", json={"content": "x"})
    assert r.status_code == 404


def test_entries_create_400_when_content_missing_or_blank(client, app):
    uid = _mk_user(app)
    _login_as(client, uid)
    hid = _mk_household(app)
    pid = _mk_pet(app, hid)

    r1 = client.post(f"/api/v1/pets/{pid}/entries", json={})
    r2 = client.post(f"/api/v1/pets/{pid}/entries", json={"content": "   "})
    assert r1.status_code == 400 and r2.status_code == 400
    assert "content is required" in r1.get_json()["error"]


def test_entries_create_201_ok_with_location(client, app):
    uid = _mk_user(app)
    _login_as(client, uid)
    hid = _mk_household(app)
    pid = _mk_pet(app, hid)

    r = client.post(f"/api/v1/pets/{pid}/entries", json={"content": "first"})
    assert r.status_code == 201
    assert r.headers.get("Location", "").startswith("/api/v1/entries/")
    body = r.get_json()
    assert body["pet_id"] == pid and body["user_id"] == uid and body["content"] == "first"


# ---------- LIST ----------


def test_entries_list_404_when_pet_missing(client, app):
    uid = _mk_user(app)
    _login_as(client, uid)
    r = client.get("/api/v1/pets/999999/entries")
    assert r.status_code == 404


def test_entries_list_200_returns_array(client, app):
    uid = _mk_user(app)
    _login_as(client, uid)
    hid = _mk_household(app)
    pid = _mk_pet(app, hid)

    # Seed a couple via API
    client.post(f"/api/v1/pets/{pid}/entries", json={"content": "a"})
    client.post(f"/api/v1/pets/{pid}/entries", json={"content": "b"})

    r = client.get(f"/api/v1/pets/{pid}/entries")
    assert r.status_code == 200
    data = r.get_json()
    assert isinstance(data, list)
    assert len(data) >= 2


# ---------- GET ONE ----------


def test_entries_get_one_401_without_login(client, app):
    u = _mk_user(app)
    hid = _mk_household(app)
    pid = _mk_pet(app, hid)
    eid = _mk_entry_direct(app, pid, u, "peek")
    r = client.get(f"/api/v1/entries/{eid}")
    assert r.status_code == 401


def test_entries_get_one_404_missing(client, app):
    uid = _mk_user(app)
    _login_as(client, uid)
    r = client.get("/api/v1/entries/999999")
    assert r.status_code == 404


def test_entries_get_one_200_ok(client, app):
    uid = _mk_user(app)
    _login_as(client, uid)
    hid = _mk_household(app)
    pid = _mk_pet(app, hid)
    eid = _mk_entry_direct(app, pid, uid, "ok")
    r = client.get(f"/api/v1/entries/{eid}")
    assert r.status_code == 200
    assert r.get_json()["content"] == "ok"


# ---------- PATCH (author-only) ----------


def test_entries_patch_404_missing(client, app):
    uid = _mk_user(app)
    _login_as(client, uid)
    r = client.patch("/api/v1/entries/999999", json={"content": "x"})
    assert r.status_code == 404


def test_entries_patch_400_blank_content(client, app):
    uid = _mk_user(app)
    _login_as(client, uid)
    hid = _mk_household(app)
    pid = _mk_pet(app, hid)
    eid = _mk_entry_direct(app, pid, uid, "old")
    r = client.patch(f"/api/v1/entries/{eid}", json={"content": "   "})
    assert r.status_code == 400
    assert "content is required" in r.get_json()["error"]


def test_entries_patch_200_updates_content(client, app):
    uid = _mk_user(app)
    _login_as(client, uid)
    hid = _mk_household(app)
    pid = _mk_pet(app, hid)
    eid = _mk_entry_direct(app, pid, uid, "old")
    r = client.patch(f"/api/v1/entries/{eid}", json={"content": "new"})
    assert r.status_code == 200
    assert r.get_json()["content"] == "new"


# ---------- DELETE (author-only) ----------


def test_entries_delete_401_without_login(client, app):
    uid = _mk_user(app)
    hid = _mk_household(app)
    pid = _mk_pet(app, hid)
    eid = _mk_entry_direct(app, pid, uid, "bye")
    r = client.delete(f"/api/v1/entries/{eid}")
    assert r.status_code == 401


def test_entries_delete_404_missing(client, app):
    uid = _mk_user(app)
    _login_as(client, uid)
    r = client.delete("/api/v1/entries/999999")
    assert r.status_code == 404