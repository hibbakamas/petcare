"""Households UI: index, create/join/leave flows, validation, and dashboard."""

import re
from app.models import Users


def test_households_index_shows_memberships(client, login_ui, make_household, add_member):
    login_ui("u1", "pw")
    h = make_household(name="My Home", join_code="HOME12")
    user = Users.query.filter_by(username="u1").first()
    add_member(user, h, nickname="Boss")

    r = client.get("/households")
    assert r.status_code == 200
    assert b"My Home" in r.data
    assert b"Boss" in r.data


def test_create_household_flow(client, login_ui):
    login_ui("maker", "pw")

    r = client.get("/households/new")
    assert r.status_code == 200

    r = client.post(
        "/households/new",
        data={"name": "Nest", "nickname": "Owner"},
        follow_redirects=False,
    )
    assert r.status_code == 302
    assert "/households/" in r.headers["Location"]


def test_join_invalid_code_blank_and_unknown(client, login_ui):
    login_ui("joiner", "pw")

    r = client.post("/join", data={"code": ""})
    assert r.status_code == 200
    assert b"Join code is required" in r.data

    r = client.post("/join", data={"code": "ZZZZZZ"}, follow_redirects=True)
    assert r.status_code == 200
    assert b"Invalid join code" in r.data


def test_join_valid_code(client, login_ui, make_household):
    login_ui("joiner2", "pw")
    h = make_household(name="Club", join_code="ABC123")

    r = client.post("/join", data={"code": "ABC123", "nickname": "Nick"}, follow_redirects=False)
    assert r.status_code == 302
    assert f"/households/{h.id}" in r.headers["Location"]


def test_households_requires_login(client):
    r = client.get("/households", follow_redirects=False)
    assert r.status_code in (302, 303)


def test_create_household_validation(client, login_ui):
    login_ui("u_hh", "pw")

    r = client.post("/households/new", data={"name": "", "nickname": ""})
    assert r.status_code == 200
    assert b"Household name is required" in r.data


def test_create_join_leave_flow(client, login_ui):
    # Owner creates household
    login_ui("owner1", "pw")
    r = client.post("/households/new", data={"name": "HH-UI", "nickname": "Owner"})
    assert r.status_code in (302, 303)

    # Read join code from dashboard
    dash = client.get("/households/1")
    assert dash.status_code == 200
    assert b"Join code:" in dash.data

    # Second user joins using the code
    client.get("/logout")
    login_ui("guest1", "pw")
    d2 = client.get("/households/1")
    txt = d2.get_data(as_text=True)
    m = re.search(r"Join code:\s*<strong>([A-Z0-9]{6})</strong>", txt)
    assert m, "join code not found in page"
    code = m.group(1)

    r = client.post("/join", data={"code": code, "nickname": "G"})
    assert r.status_code in (302, 303)

    # Guest leaves
    r = client.post("/households/1/leave", data={})
    assert r.status_code in (302, 303)


def test_households_new_validation_and_404(client, login_ui):
    login_ui("ui_hh_user", "pw")

    r = client.post("/households/new", data={"name": ""})
    assert r.status_code == 200
    assert b"Household name is required" in r.data

    r = client.get("/households/999999")
    assert r.status_code == 404


def test_join_invalid_code_when_already_member(client, login_ui, make_household, add_member):
    login_ui("join_user", "pw")

    # Set up membership then try joining again with same code/nickname
    u = Users.query.filter_by(username="join_user").first()
    h = make_household(name="UIHH2", join_code="HHC0DE")
    add_member(u, h, nickname="Me")

    r = client.post("/join", data={"code": "HHC0DE", "nickname": "Me"})
    assert r.status_code == 200
    assert b"already a member" in r.data