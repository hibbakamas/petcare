# tests/ui/test_users_ui.py

def test_profile_get_and_update_username(client, login_ui):
    login_ui("oldname", "pw")
    r = client.get("/profile")
    assert r.status_code == 200
    assert b"oldname" in r.data

    # update to new unique username
    r2 = client.post("/profile/username", data={"username": "newname"}, follow_redirects=False)
    assert r2.status_code == 302

    # profile now shows new name
    r3 = client.get("/profile")
    assert b"newname" in r3.data

def test_profile_update_username_validation(client, login_ui):
    # make two users
    login_ui("alice", "pw")
    client.get("/logout")
    login_ui("bob", "pw")

    # try to change bob to "alice" (duplicate)
    r = client.post("/profile/username", data={"username": "alice"}, follow_redirects=True)
    assert r.status_code in (200, 409)
    assert b"already taken" in r.data

def test_profile_update_household_nickname(client, login_ui, make_household, add_member):
    login_ui("nicku", "pw")
    from app.models import Users
    u = Users.query.filter_by(username="nicku").first()
    h = make_household(name="NickHouse", join_code="NICK12")
    m = add_member(u, h, nickname="OldNick")

    r = client.post(f"/households/{h.id}/nickname", data={"nickname": "NewNick"}, follow_redirects=False)
    assert r.status_code == 302

    # check page shows updated nickname
    r2 = client.get("/profile")
    assert b"NewNick" in r2.data

def test_profile_username_update_and_duplicate(client, login_ui, make_user):
    # create an existing taken username
    make_user(username="taken", password="x")

    login_ui("meuser", "pw")
    r = client.get("/profile")
    assert r.status_code == 200

    # empty -> error
    r = client.post("/profile/username", data={"username": ""})
    assert r.status_code == 200
    assert b"Username cannot be empty" in r.data

    # duplicate -> error
    r = client.post("/profile/username", data={"username": "taken"})
    assert r.status_code == 200
    assert b"That username is already taken" in r.data

    # success
    r = client.post("/profile/username", data={"username": "newname"})
    assert r.status_code in (302, 303)

def test_profile_username_validation_and_taken(client, login_ui, make_user):
    login_ui("name_old", "pw")

    # empty -> 200 + error on page
    r = client.post("/profile/username", data={"username": ""})
    assert r.status_code == 200
    assert b"Username cannot be empty" in r.data

    # taken
    make_user(username="taken_user", password="pw")
    r = client.post("/profile/username", data={"username": "taken_user"})
    assert r.status_code == 200
    assert b"already taken" in r.data

def test_profile_nickname_validation_and_dup_in_household(client, login_ui, make_household, add_member):
    # owner user + household
    login_ui("nick_owner", "pw")
    from app.models import Users
    u = Users.query.filter_by(username="nick_owner").first()
    h = make_household(name="NickHH", join_code="NICK01")
    add_member(u, h, nickname="Owner")

    # empty nickname -> validation message
    r = client.post(f"/households/{h.id}/nickname", data={"nickname": ""})
    assert r.status_code == 200
    assert b"cannot be empty" in r.data

    # second user joins with a different nickname first
    client.get("/logout")
    login_ui("nick_other", "pw")
    u2 = Users.query.filter_by(username="nick_other").first()
    add_member(u2, h, nickname="OtherNick")

    # now try to change u2's nickname to the conflicting one -> IntegrityError path
    r = client.post(f"/households/{h.id}/nickname", data={"nickname": "Owner"})
    assert r.status_code == 200
    assert b"already used in this household" in r.data