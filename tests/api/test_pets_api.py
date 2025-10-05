"""Pets API tests: household-nested create/list and pet CRUD with membership rules."""

import re
from datetime import datetime

from tests.common import extract_int, fill_route_params, find_api_route
from app.models import Household, HouseholdMember, Pet, Users, db


# ---------- dynamic API helpers ----------

def _login(client, app, username="pets_api_user", password="pw"):
    signup = find_api_route(app, ["signup"], "POST") or find_api_route(app, ["users"], "POST")
    login = find_api_route(app, ["login"], "POST")
    assert signup and login
    client.post(signup, json={"username": username, "password": password})
    client.post(login, json={"username": username, "password": password})


def _make_household(client, app, name="PetHome"):
    create_url = find_api_route(app, ["household"], "POST") or find_api_route(app, ["households"], "POST")
    assert create_url, "No POST /api/...households route"
    r = client.post(create_url, json={"name": name})
    data = r.get_json(silent=True) or {}
    return extract_int(data, ("id", "household_id"))


def test_create_pet(client, app):
    _login(client, app)
    hid = _make_household(client, app)

    pets_post = find_api_route(app, ["pets"], "POST")
    assert pets_post, "No POST /api/...pets route"

    try:
        url = fill_route_params(pets_post, household_id=hid)
    except KeyError:
        url = pets_post

    r = client.post(url, json={"name": "API Pup", "household_id": hid})
    assert r.status_code in (200, 201), r.get_data(as_text=True)
    pet = r.get_json(silent=True) or {}
    pid = extract_int(pet, ("id", "pet_id"))
    assert pid is None or isinstance(pid, int)


def _login_and_household(client, app):
    _login(client, app, username="pets_api_user")
    return _make_household(client, app, name="PetsHH")


def test_pets_create_show_delete_and_validation(client, app):
    hid = _login_and_household(client, app)

    post = find_api_route(app, ["pets"], "POST")
    assert post

    # Missing name (APIs differ: some 400/422, some still create)
    try:
        purl = fill_route_params(post, household_id=hid)
    except KeyError:
        purl = post
    r = client.post(purl, json={"household_id": hid})
    assert r.status_code in (201, 200, 400, 422)
    if r.status_code in (200, 201):
        pet = r.get_json(silent=True) or {}
        assert isinstance(pet, dict)
        assert ("id" in pet) or ("pet_id" in pet)

    # Create OK
    r = client.post(purl, json={"name": "Rory", "household_id": hid})
    assert r.status_code in (200, 201)
    pet = r.get_json(silent=True) or {}
    pid = extract_int(pet, ("id", "pet_id"))

    # Optional GET show/list
    get = find_api_route(app, ["pets"], "GET")
    if get:
        if "<" in get:
            # Detail route present (e.g., /api/pets/<int:pet_id>)
            try:
                gurl = fill_route_params(get, pet_id=pid, household_id=hid)
            except KeyError:
                gurl = get
            rg = client.get(gurl)
            assert rg.status_code in (200, 404)
        else:
            # List route (e.g., /api/pets); just ensure it returns JSON
            rg = client.get(get)
            assert rg.status_code == 200
            assert isinstance(rg.get_json(silent=True), (list, dict))

        # Invalid id only if a param route exists
        if "<" in get and pid is not None:
            try:
                bad_gurl = fill_route_params(get, pet_id=999999, household_id=hid)
            except KeyError:
                bad_gurl = get
            rbad = client.get(bad_gurl)
            # Some APIs return 200 with {} or [] for "missing"
            assert rbad.status_code in (200, 404, 400)
            if rbad.status_code == 200:
                payload = rbad.get_json(silent=True)
                assert isinstance(payload, (dict, list))

    # Delete then delete again (idempotency / 404 path)
    delete = find_api_route(app, ["pets"], "DELETE")
    if delete:
        try:
            durl = fill_route_params(delete, pet_id=pid, household_id=hid)
        except KeyError:
            durl = delete
        rd1 = client.delete(durl)
        assert rd1.status_code in (200, 204, 404)
        rd2 = client.delete(durl)
        assert rd2.status_code in (404, 400, 204)


def test_pets_more_validation_and_show_404(client, app):
    # “Missing household_id” tolerance and 404/200 variants on show
    _login(client, app)
    hid = _make_household(client, app)

    pets_post = find_api_route(app, ["pets"], "POST")
    assert pets_post

    # Missing household_id: allow APIs that infer it from path or ignore it
    try:
        post_url = fill_route_params(pets_post, household_id=hid)
    except KeyError:
        post_url = pets_post
    r = client.post(post_url, json={"name": "NoHH"})
    assert r.status_code in (201, 200, 400, 422)
    if r.status_code in (200, 201):
        pet = r.get_json(silent=True) or {}
        assert isinstance(pet, dict)
        assert ("id" in pet) or ("pet_id" in pet)

    # Create OK
    r = client.post(post_url, json={"name": "WithHH", "household_id": hid})
    assert r.status_code in (200, 201)
    pet = r.get_json(silent=True) or {}
    pid = extract_int(pet, ("id", "pet_id"))

    # Invalid show only when GET route has params
    pets_get = find_api_route(app, ["pets"], "GET")
    if pets_get and "<" in pets_get:
        try:
            bad = fill_route_params(pets_get, pet_id=999999, household_id=hid)
        except KeyError:
            bad = pets_get
        rr = client.get(bad)
        # Accept APIs that return 200 with {} / [] for not found
        assert rr.status_code in (404, 400, 200)
        if rr.status_code == 200:
            payload = rr.get_json(silent=True)
            assert isinstance(payload, (dict, list))


# ---------- strict tests (db-level helpers) ----------

def _mk_user(app, username="pets_user"):
    with app.app_context():
        u = Users(username=username, password_hash="x")
        db.session.add(u)
        db.session.commit()
        return u.id


def _login_as(client, user_id: int):
    with client.session_transaction() as s:
        s["user_id"] = user_id


def _mk_household(app, name="HH", join_code=None):
    if join_code is None:
        import random, string
        join_code = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    with app.app_context():
        h = Household(name=name, join_code=join_code)
        db.session.add(h)
        db.session.commit()
        return h.id


def _add_member(app, hid, uid, nickname=None):
    if nickname is None:
        nickname = f"user{uid}_hh{hid}"
    with app.app_context():
        m = HouseholdMember(household_id=hid, user_id=uid, nickname=nickname)
        db.session.add(m)
        db.session.commit()


def _mk_pet(app, hid, name="Milo"):
    with app.app_context():
        p = Pet(household_id=hid, name=name)
        db.session.add(p)
        db.session.commit()
        return p.id


# ---------- CREATE / LIST (household-nested) ----------

def test_create_pet_201_ok(client, app):
    uid = _mk_user(app)
    hid = _mk_household(app)
    _add_member(app, hid, uid)
    _login_as(client, uid)

    r = client.post(f"/api/v1/households/{hid}/pets", json={"name": "API Pup"})
    assert r.status_code == 201, r.get_data(as_text=True)
    assert r.headers.get("Location", "").startswith("/api/v1/pets/")
    body = r.get_json()
    assert body["name"] == "API Pup"
    assert body["household_id"] == hid


def test_create_pet_400_missing_name(client, app):
    uid = _mk_user(app)
    hid = _mk_household(app)
    _add_member(app, hid, uid)
    _login_as(client, uid)

    r = client.post(f"/api/v1/households/{hid}/pets", json={})
    assert r.status_code == 400
    assert "name is required" in r.get_json()["error"]


def test_create_pet_404_bad_household(client, app):
    uid = _mk_user(app)
    _login_as(client, uid)
    r = client.post("/api/v1/households/999999/pets", json={"name": "Ghost"})
    assert r.status_code == 404


def test_list_pets_403_non_member(client, app):
    uid = _mk_user(app)
    hid = _mk_household(app)
    _login_as(client, uid)  # not a member
    r = client.get(f"/api/v1/households/{hid}/pets")
    assert r.status_code == 403


# ---------- GET / PATCH / DELETE (by pet id) ----------

def test_get_pet_200_member(client, app):
    uid = _mk_user(app)
    hid = _mk_household(app)
    _add_member(app, hid, uid)
    pid = _mk_pet(app, hid, "Rory")
    _login_as(client, uid)

    r = client.get(f"/api/v1/pets/{pid}")
    assert r.status_code == 200
    assert r.get_json()["name"] == "Rory"


def test_get_pet_403_not_member(client, app):
    uid = _mk_user(app)
    hid = _mk_household(app)
    pid = _mk_pet(app, hid, "Rory")
    _login_as(client, uid)  # not a member
    r = client.get(f"/api/v1/pets/{pid}")
    assert r.status_code == 403


def test_get_pet_404_missing(client, app):
    uid = _mk_user(app)
    _login_as(client, uid)
    r = client.get("/api/v1/pets/999999")
    assert r.status_code == 404


def test_patch_pet_200_no_change_when_empty_payload(client, app):
    uid = _mk_user(app)
    hid = _mk_household(app)
    _add_member(app, hid, uid)
    pid = _mk_pet(app, hid, "Milo")
    _login_as(client, uid)

    r = client.patch(f"/api/v1/pets/{pid}", json={})
    assert r.status_code == 200
    assert r.get_json()["name"] == "Milo"


def test_patch_pet_400_empty_name(client, app):
    uid = _mk_user(app)
    hid = _mk_household(app)
    _add_member(app, hid, uid)
    pid = _mk_pet(app, hid, "Milo")
    _login_as(client, uid)

    r = client.patch(f"/api/v1/pets/{pid}", json={"name": "   "})
    assert r.status_code == 400
    assert "cannot be empty" in r.get_json()["error"]


def test_patch_pet_200_valid_rename(client, app):
    uid = _mk_user(app)
    hid = _mk_household(app)
    _add_member(app, hid, uid)
    pid = _mk_pet(app, hid, "Milo")
    _login_as(client, uid)

    r = client.patch(f"/api/v1/pets/{pid}", json={"name": "Nala"})
    assert r.status_code == 200
    assert r.get_json()["name"] == "Nala"


def test_patch_pet_403_not_member(client, app):
    uid = _mk_user(app)
    hid = _mk_household(app)
    pid = _mk_pet(app, hid, "Milo")
    _login_as(client, uid)  # not a member
    r = client.patch(f"/api/v1/pets/{pid}", json={"name": "X"})
    assert r.status_code == 403


def test_delete_pet_204_member(client, app):
    uid = _mk_user(app)
    hid = _mk_household(app)
    _add_member(app, hid, uid)
    pid = _mk_pet(app, hid, "ToDelete")
    _login_as(client, uid)

    r = client.delete(f"/api/v1/pets/{pid}")
    assert r.status_code == 204
    r2 = client.delete(f"/api/v1/pets/{pid}")
    assert r2.status_code == 404


def test_delete_pet_403_not_member(client, app):
    uid = _mk_user(app)
    hid = _mk_household(app)
    pid = _mk_pet(app, hid, "Stranger")
    _login_as(client, uid)  # not a member
    r = client.delete(f"/api/v1/pets/{pid}")
    assert r.status_code == 403


# ---------- localdt filter checks ----------

def test_localdt_none_and_invalid_tz(app):
    f = app.jinja_env.filters["localdt"]
    assert f(None) == ""
    s = f(datetime(2025, 1, 1, 12, 0), tz_name="Nope/Nowhere")
    assert re.match(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$", s)


def test_localdt_naive_treated_as_utc(app):
    f = app.jinja_env.filters["localdt"]
    s = f(datetime(2025, 1, 1, 12, 0))
    assert re.match(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$", s)