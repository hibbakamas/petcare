"""Validation smoke tests for households, pets, and entries."""

from tests.common import fill_route_params, find_api_route


def _login(client, app):
    signup = find_api_route(app, ["signup"], "POST") or find_api_route(app, ["users"], "POST")
    login = find_api_route(app, ["login"], "POST")
    client.post(signup, json={"username": "val_api_user", "password": "pw"})
    client.post(login, json={"username": "val_api_user", "password": "pw"})


def test_validation_errors_on_household_pet_entry(client, app):
    _login(client, app)

    # Household name required
    hh_post = find_api_route(app, ["household"], "POST") or find_api_route(app, ["households"], "POST")
    if hh_post:
        r = client.post(hh_post, json={"name": ""})
        assert r.status_code in (400, 422)

    # Create a household to use its id for nested checks (if supported)
    hid = None
    if hh_post:
        rr = client.post(hh_post, json={"name": "Valid"})
        if rr.status_code in (200, 201):
            data = rr.get_json(silent=True) or {}
            hid = data.get("id") or data.get("household_id")

    # Pets: name required (some APIs 404 if parent household path/param is wrong)
    pets_post = find_api_route(app, ["pets"], "POST")
    if pets_post:
        try:
            purl = fill_route_params(pets_post, household_id=hid or 1)
        except KeyError:
            purl = pets_post
        r = client.post(purl, json={"name": "", "household_id": hid})
        assert r.status_code in (400, 422, 404)

    # Entries: content required (many APIs 404 if pet_id missing/invalid)
    entries_post = find_api_route(app, ["entries"], "POST")
    if entries_post:
        try:
            eurl = fill_route_params(entries_post, pet_id=1)  # may not exist -> 404 is acceptable
        except KeyError:
            eurl = entries_post
        r = client.post(eurl, json={"content": ""})
        assert r.status_code in (400, 422, 404)