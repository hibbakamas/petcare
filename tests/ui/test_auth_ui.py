# tests/ui/test_auth_ui.py

def test_signup_then_logout_then_login(client):
    # signup
    r = client.post("/signup", data={"username": "hibs", "password": "pw"}, follow_redirects=False)
    assert r.status_code == 302 and "/households" in r.headers["Location"]

    # logout (GET link)
    r = client.get("/logout", follow_redirects=False)
    assert r.status_code == 302 and "/login" in r.headers["Location"]

    # login
    r = client.post("/login", data={"username": "hibs", "password": "pw"}, follow_redirects=False)
    assert r.status_code == 302 and "/households" in r.headers["Location"]

def test_login_bad_creds(client):
    r = client.post("/login", data={"username": "nope", "password": "wrong"}, follow_redirects=True)
    assert r.status_code == 401
    assert b"Invalid username or password" in r.data

def test_signup_duplicate_username(client):
    # first signup
    r1 = client.post("/signup", data={"username": "dupe", "password": "pw"})
    assert r1.status_code == 302
    # second with same username
    r2 = client.post("/signup", data={"username": "dupe", "password": "pw"}, follow_redirects=True)
    assert r2.status_code == 409
    assert b"That username is taken" in r2.data