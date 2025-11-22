"""Health and metrics endpoints for monitoring and observability."""

def test_health_endpoint_ok(client):
    r = client.get("/health")
    assert r.status_code == 200
    data = r.get_json()
    assert isinstance(data, dict)
    assert data.get("status") == "ok"


def test_metrics_endpoint_exposes_prometheus_text(client):
    r = client.get("/metrics")
    # Prometheus client uses a text/plain content type with version info.
    assert r.status_code == 200
    assert r.mimetype.startswith("text/plain")
    body = r.get_data(as_text=True)
    # Our custom metric names should appear in the body.
    assert "petcare_request_total" in body