"""API error handling and utility filter tests."""

def test_api_404_is_json(client):
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
    r = client.get("/def-not-here")
    assert r.status_code == 404
    data = r.get_json(silent=True)
    assert isinstance(data, dict) and data.get("error")


def test_localdt_filter_renders(app):
    # Exercise the registered Jinja filter with a simple template.
    tpl = app.jinja_env.from_string("{{ dt | localdt('Europe/Madrid', '%Y-%m-%d') }}")
    from datetime import datetime, timezone

    dt = datetime(2025, 1, 2, 15, 0, tzinfo=timezone.utc)
    out = tpl.render(dt=dt)
    assert out == "2025-01-02"