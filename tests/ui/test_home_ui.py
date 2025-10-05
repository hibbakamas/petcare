"""Home UI: redirects based on session."""

def test_home_redirects_logged_out(client):
    r = client.get("/", follow_redirects=False)
    assert r.status_code == 302
    assert "/login" in r.headers["Location"]


def test_home_redirects_logged_in(client, login_ui):
    login_ui()
    r = client.get("/", follow_redirects=False)
    assert r.status_code == 302
    assert "/households" in r.headers["Location"]