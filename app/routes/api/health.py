"""Simple API health-check endpoint."""

from flask import Blueprint, jsonify

bp = Blueprint("health_api", __name__, url_prefix="/api")


@bp.get("/health")
def health():
    """Return a basic JSON health status for monitoring."""
    return jsonify(status="ok"), 200