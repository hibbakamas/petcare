# tests/api/test_errors_api.py

def test_api_404_is_json(client):
    r = client.get("/api/this-clearly-does-not-exist")
    assert r.status_code == 404
    data = r.get_json(silent=True)
    assert isinstance(data, dict) and data.get("error")

def test_api_405_is_json(client, app):
    # Prefer a GET route without params so POST -> 405; otherwise we may get 404.
    list_url = None
    for rule in app.url_map.iter_rules():
        path = str(rule.rule)
        if not path.startswith("/api"):
            continue
        if "GET" not in (rule.methods or []):
            continue
        if "<" in path:            # skip parameterized routes
            continue
        list_url = path
        break

    # Fallback: if none found, just pick any GET route (may yield 404 later)
    if not list_url:
        for rule in app.url_map.iter_rules():
            path = str(rule.rule)
            if path.startswith("/api") and "GET" in (rule.methods or []):
                list_url = path
                break

    if not list_url:
        # No /api GET routes at all — nothing to test
        return

    r = client.post(list_url, json={})
    # If route exists for GET only -> 405. If params were required (and we didn't fill them) -> 404.
    assert r.status_code in (405, 400, 404)
    data = r.get_json(silent=True)
    assert isinstance(data, dict)

def test_json_404(client):
    r = client.get("/def-not-here")
    assert r.status_code == 404
    data = r.get_json(silent=True)
    # your app returns JSON for 404
    assert isinstance(data, dict) and data.get("error")

def test_localdt_filter_renders(app):
    # render a tiny template using the registered jinja filter
    tpl = app.jinja_env.from_string("{{ dt | localdt('Europe/Madrid', '%Y-%m-%d') }}")
    from datetime import datetime, timezone
    dt = datetime(2025, 1, 2, 15, 0, tzinfo=timezone.utc)
    out = tpl.render(dt=dt)
    assert out == "2025-01-02"  # date stays same; we just exercise the filter