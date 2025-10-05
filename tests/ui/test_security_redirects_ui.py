# tests/ui/test_security_redirects_ui.py

def test_protected_pages_redirect_to_login_when_logged_out(client):
    # all these should 302 to /login when no session user_id
    protected_gets = [
        "/households",
        "/households/new",
        "/profile",
    ]
    for path in protected_gets:
        r = client.get(path, follow_redirects=False)
        assert r.status_code == 302
        assert "/login" in r.headers["Location"]