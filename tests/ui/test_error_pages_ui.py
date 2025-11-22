"""App-level error pages: UI should get HTML, API gets JSON (API covered elsewhere)."""

def test_404_unknown_path_returns_html(client):
    """
    For a non-/api UI path, the app should render an HTML 404 page,
    not a JSON error payload.
    """
    r = client.get("/totally-unknown-path-xyz")
    assert r.status_code == 404
    assert r.mimetype == "text/html"
    # We don't depend on the exact wording, just that there is some body.
    body = r.get_data(as_text=True)
    assert body
    # Optional: very loose check that it's a 404 page.
    assert "404" in body or "Not Found" in body


def test_405_method_not_allowed_on_logout(client):
    """
    /logout is a UI route. If POST isn't allowed, either:
    - the app redirects (302) to login, or
    - the app returns an HTML 405 page.
    """
    r = client.post("/logout")

    assert r.status_code in (405, 302)

    if r.status_code == 302:
        # Typical behavior: redirect back to /login when misused.
        assert "/login" in r.headers["Location"]
    else:
        # 405 HTML error page.
        assert r.mimetype == "text/html"
        body = r.get_data(as_text=True)
        assert body
        assert "405" in body or "Method Not Allowed" in body