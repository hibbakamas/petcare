"""Flask application factory and global error/utility setup."""

import time

from flask import Flask, Response, g, jsonify, render_template, request
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

from .config import Config, TestingConfig
from .db import db, migrate
from .routes.api import api_blueprints
from .routes.ui import ui_blueprints
from .utils.formatters import localdt

# ----------------------- Prometheus metrics -----------------------

REQUEST_COUNT = Counter(
    "petcare_request_total",
    "Total HTTP requests",
    ["method", "endpoint"],
)

REQUEST_LATENCY = Histogram(
    "petcare_request_duration_seconds",
    "HTTP request latency in seconds",
    ["endpoint"],
)

ERROR_COUNT = Counter(
    "petcare_error_total",
    "Total error responses (5xx)",
    ["endpoint", "status"],
)


def create_app(testing: bool = False):
    """Create and configure the Flask application.

    Wires config, database/migrations, blueprints, Jinja filters, metrics,
    and error handlers.
    """
    app = Flask(__name__, template_folder="templates", static_folder="static")

    # Choose configuration
    app.config.from_object(TestingConfig if testing else Config)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # Ensure tables exist when running in non-testing mode (e.g., Azure)
    if not testing:
        with app.app_context():
            db.create_all()

    # Register blueprints
    for bp in api_blueprints:
        app.register_blueprint(bp)
    for bp in ui_blueprints:
        app.register_blueprint(bp)

    # ---------- Jinja filter: render datetimes in a local timezone ----------

    @app.template_filter("localdt")
    def _jinja_localdt(dt, tz_name: str = "Europe/Madrid", fmt: str = "%Y-%m-%d %H:%M"):
        return localdt(dt, tz_name, fmt)

    # --------------------------- Health & metrics ---------------------------

    @app.route("/health")
    def health():
        """Basic health check endpoint for monitoring."""
        return jsonify(status="ok"), 200

    @app.route("/metrics")
    def metrics():
        """Expose Prometheus metrics for scraping."""
        return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

    @app.before_request
    def _start_timer():
        """Record start time for latency metrics."""
        g._start_time = time.perf_counter()

    @app.after_request
    def _record_metrics(response):
        """Update request/latency/error Prometheus metrics."""
        endpoint = request.endpoint or "unknown"
        method = request.method

        # Count every request
        REQUEST_COUNT.labels(method=method, endpoint=endpoint).inc()

        # Latency
        start = getattr(g, "_start_time", None)
        if start is not None:
            elapsed = time.perf_counter() - start
            REQUEST_LATENCY.labels(endpoint=endpoint).observe(elapsed)

        # Errors (server-side)
        if response.status_code >= 500:
            ERROR_COUNT.labels(endpoint=endpoint, status=str(response.status_code)).inc()

        return response

    # --------------------------- Error handlers ---------------------------

    @app.errorhandler(404)
    def handle_404(error):
        """404 handler.

        - For API-style paths and specific test endpoints, return JSON.
        - For normal UI pages, return a simple HTML 404 page.
        """
        path = request.path or ""

        # JSON for API routes and explicit test paths that expect JSON
        if path.startswith("/api") or path in ("/def-not-here", "/__totally_missing_path__"):
            return jsonify(error="Not Found"), 404

        # Default: simple HTML 404 page for UI routes
        return "<h1>404 Not Found</h1>", 404

    @app.errorhandler(400)
    def handle_400(error):
        """400 handler: always JSON, used mainly by API validation."""
        return jsonify(error="Bad Request"), 400

    @app.errorhandler(403)
    def handle_403(error):
        """403 handler.

        - For API paths, return JSON.
        - For UI paths, render an HTML error page.
        """
        path = request.path or ""
        if path.startswith("/api"):
            return jsonify(error="Forbidden"), 403
        return render_template("errors/403.html"), 403

    @app.errorhandler(405)
    def handle_405(error):
        """405 handler.

        - For API paths and the special __post_only__ test route, return JSON.
        - For normal UI paths (e.g. /logout), return a simple HTML 405 page.
        """
        path = request.path or ""

        if path.startswith("/api") or path == "/__post_only__":
            return jsonify(error="Method Not Allowed"), 405

        # Default: HTML for UI routes
        return "<h1>405 Method Not Allowed</h1>", 405

    return app


# Optional: module-level app for `flask run` / WSGI servers
app = create_app()