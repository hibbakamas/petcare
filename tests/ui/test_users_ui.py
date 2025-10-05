"""Users UI: profile view, username updates, nickname updates, and validation."""

from app.models import Users


def test_profile_get_and_update_username(client, login_ui):
    login_ui("oldname", "pw")

    r = client.get("/profile")
    assert r.status_code == 200
    assert b"oldname" in r.data

    r2 = client.post("/profile/username", data={"username": "newname"}, follow_redirects=False)
    assert r2.status_code == 302

    r3 = client.get("/profile")
    assert b"newname" in r3.data


def test_profile_update_username_validation(client, login_ui):
    login_ui("alice", "pw")
    client.get("/logout")
    login_ui("bob", "pw")

    r = client.post("/profile/username", data={"username": "alice"}, follow_redirects=True)
    assert r.status_code in (200, 409)
    assert b"already taken" in r.data


def test_profile_update_household_nickname(client, login_ui, make_household, add_member):
    login_ui("nicku", "pw")
    u = Users.query.filter_by(username="nicku").first()
    h = make_household(name="NickHouse", join_code="NICK12")
    add_member(u, h, nickname="OldNick")

    r = client.post(f"/households/{h.id}/nickname", data={"nickname": "NewNick"}, follow_redirects=False)
    assert r.status_code == 302

    r2 = client.get("/profile")
    assert b"NewNick" in r2.data


def test_profile_username_update_and_duplicate(client, login_ui, make_user):
    make_user(username="taken", password="x")

    login_ui("meuser", "pw")
    r = client.get("/profile")
    assert r.status_code == 200

    r = client.post("/profile/username", data={"username": ""})
    assert r.status_code == 200
    assert b"Username cannot be empty" in r.data

    r = client.post("/profile/username", data={"username": "taken"})
    assert r.status_code == 200
    assert b"That username is already taken" in r.data

    r = client.post("/profile/username", data={"username": "newname"})
    assert r.status_code in (302, 303)


def test_profile_username_validation_and_taken(client, login_ui, make_user):
    login_ui("name_old", "pw")

    r = client.post("/profile/username", data={"username": ""})
    assert r.status_code == 200
    assert b"Username cannot be empty" in r.data

    make_user(username="taken_user", password="pw")
    r = client.post("/profile/username", data={"username": "taken_user"})
    assert r.status_code == 200
    assert b"already taken" in r.data


def test_profile_nickname_validation_and_dup_in_household(client, login_ui, make_household, add_member):
    login_ui("nick_owner", "pw")
    u = Users.query.filter_by(username="nick_owner").first()
    h = make_household(name="NickHH", join_code="NICK01")
    add_member(u, h, nickname="Owner")

    r = client.post(f"/households/{h.id}/nickname", data={"nickname": ""})
    assert r.status_code == 200
    assert b"cannot be empty" in r.data

    client.get("/logout")
    login_ui("nick_other", "pw")
    u2 = Users.query.filter_by(username="nick_other").first()
    add_member(u2, h, nickname="OtherNick")

    r = client.post(f"/households/{h.id}/nickname", data={"nickname": "Owner"})
    assert r.status_code == 200
    assert b"already used in this household" in r.data