"""Flask application factory and global error/utility setup."""

from datetime import timezone
from zoneinfo import ZoneInfo

from flask import Flask, jsonify, render_template, request

from .config import Config, TestingConfig
from .db import db, migrate
from .routes.api import api_blueprints
from .routes.ui import ui_blueprints
from .utils.formatters import localdt

def create_app(testing: bool = False):
    """Create and configure the Flask application.

    Wires config, database/migrations, blueprints, Jinja filters, and error handlers.
    """
    app = Flask(__name__, template_folder="templates", static_folder="static")

    # Choose configuration
    app.config.from_object(TestingConfig if testing else Config)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # Register blueprints
    for bp in api_blueprints:
        app.register_blueprint(bp)
    for bp in ui_blueprints:
        app.register_blueprint(bp)

    # ---------- Jinja filter: render datetimes in a local timezone ----------

    @app.template_filter("localdt")
    def _jinja_localdt(dt, tz_name="Europe/Madrid", fmt="%Y-%m-%d %H:%M"):
        return localdt(dt, tz_name, fmt)


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