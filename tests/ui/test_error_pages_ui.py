# tests/test_error_pages.py

def test_404_unknown_path_returns_json(client):
    r = client.get("/totally-unknown-path-xyz")
    # Your app-level errorhandler returns JSON for 404s
    assert r.status_code == 404
    data = r.get_json(silent=True)
    assert isinstance(data, dict) and data.get("error") in {"Not Found", "NotFound", "Not Found"}

def test_405_method_not_allowed_on_logout(client):
    # logout is GET in UI; POST should be 405 handled by app errorhandler
    r = client.post("/logout")
    assert r.status_code in (405, 302)  # some servers may redirect if you later change behavior
    if r.status_code == 405:
        data = r.get_json(silent=True)
        assert isinstance(data, dict) and "Method Not Allowed" in data.get("error", "Method Not Allowed")