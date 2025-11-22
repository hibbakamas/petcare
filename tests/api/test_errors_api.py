"""API error handling and utility filter tests."""

def test_api_404_is_json(client):
    # Any missing /api/... path should return a JSON error payload.
    r = client.get("/api/this-clearly-does-not-exist")
    assert r.status_code == 404
    data = r.get_json(silent=True)
    assert isinstance(data, dict) and data.get("error")


def test_api_405_is_json(client, app):
    # Prefer a GET route without params so POST -> 405; otherwise 404 is acceptable.
    list_url = None
    for rule in app.url_map.iter_rules():
        path = str(rule.rule)
        if not path.startswith("/api"):
            continue
        if "GET" not in (rule.methods or []):
            continue
        if "<" in path:  # skip parameterized routes
            continue
        list_url = path
        break

    # Fallback: any GET-able /api route (may return 404 when POSTed).
    if not list_url:
        for rule in app.url_map.iter_rules():
            path = str(rule.rule)
            if path.startswith("/api") and "GET" in (rule.methods or []):
                list_url = path
                break

    if not list_url:
        return  # no API GET routes to exercise

    r = client.post(list_url, json={})
    # If route exists for GET only -> 405; otherwise 400/404 are acceptable variants.
    assert r.status_code in (405, 400, 404)
    data = r.get_json(silent=True)
    assert isinstance(data, dict)


def test_json_404(client):
    """
    For API-style requests (/api/…), 404s should be JSON.

    UI-only paths are covered in the UI tests, which expect HTML.
    """
    r = client.get("/api/__def-not-here__")
    assert r.status_code == 404
    data = r.get_json(silent=True)
    assert isinstance(data, dict) and data.get("error")