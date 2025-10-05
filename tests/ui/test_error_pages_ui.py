"""App-level error pages: JSON 404 and 405 handling."""

def test_404_unknown_path_returns_json(client):
    r = client.get("/totally-unknown-path-xyz")
    assert r.status_code == 404
    data = r.get_json(silent=True)
    assert isinstance(data, dict)
    assert data.get("error") in {"Not Found", "NotFound"}


def test_405_method_not_allowed_on_logout(client):
    # UI logout is GET; POST should be 405 (some apps may redirect instead).
    r = client.post("/logout")
    assert r.status_code in (405, 302)
    if r.status_code == 405:
        data = r.get_json(silent=True)
        assert isinstance(data, dict)
        assert "Method Not Allowed" in data.get("error", "")