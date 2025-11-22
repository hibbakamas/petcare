"""UI-level health endpoint (plain text)."""

from flask import Blueprint

bp = Blueprint("health_ui", __name__)


@bp.get("/healthz")
def healthz():
    """Plain-text health endpoint for load balancers / uptime checks."""
    return "ok", 200, {"Content-Type": "text/plain; charset=utf-8"}