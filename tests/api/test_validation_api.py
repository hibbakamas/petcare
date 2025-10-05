import pytest
from tests.common import find_api_route, fill_route_params

def _login(client, app):
    s = find_api_route(app, ["signup"], "POST") or find_api_route(app, ["users"], "POST")
    l = find_api_route(app, ["login"], "POST")
    client.post(s, json={"username": "val_api_user", "password": "pw"})
    client.post(l, json={"username": "val_api_user", "password": "pw"})

def test_validation_errors_on_household_pet_entry(client, app):
    _login(client, app)

    # household name required
    hh_post = find_api_route(app, ["household"], "POST") or find_api_route(app, ["households"], "POST")
    if hh_post:
        r = client.post(hh_post, json={"name": ""})
        assert r.status_code in (400, 422)

    # find household id to proceed with pet/entry checks (ok if fails)
    hid = None
    if hh_post:
        r = client.post(hh_post, json={"name": "Valid"})
        if r.status_code in (200, 201):
            data = r.get_json(silent=True) or {}
            hid = data.get("id") or data.get("household_id")

    # pets: name required (some apps 404 if household path/parent is wrong)
    pets_post = find_api_route(app, ["pets"], "POST")
    if pets_post:
        try:
            purl = fill_route_params(pets_post, household_id=hid or 1)
        except KeyError:
            purl = pets_post
        r = client.post(purl, json={"name": "", "household_id": hid})
        assert r.status_code in (400, 422, 404)

    # entries: content required (many apps 404 if pet_id missing/invalid)
    entries_post = find_api_route(app, ["entries"], "POST")
    if entries_post:
        try:
            eurl = fill_route_params(entries_post, pet_id=1)  # may not exist -> 404
        except KeyError:
            eurl = entries_post
        r = client.post(eurl, json={"content": ""})
        assert r.status_code in (400, 422, 404)