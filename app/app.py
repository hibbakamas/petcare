"""Flask application factory and global error/utility setup."""

from datetime import timezone
from zoneinfo import ZoneInfo

from flask import Flask, jsonify, render_template

from .config import Config, TestingConfig
from .db import db, migrate
from .routes.api import api_blueprints
from .routes.ui import ui_blueprints


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
    def localdt(dt, tz_name: str = "Europe/Madrid", fmt: str = "%Y-%m-%d %H:%M"):
        """Render a datetime in the given IANA timezone.

        If `dt` is naive, treat it as UTC. Returns '' for None.
        """
        if dt is None:
            return ""
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        try:
            tz = ZoneInfo(tz_name)
        except Exception:
            tz = ZoneInfo("Europe/Madrid")
        return dt.astimezone(tz).strftime(fmt)

    # --------------------------- JSON error handlers ---------------------------
    @app.errorhandler(404)
    def not_found(e):
        return jsonify(error="Not Found"), 404

    @app.errorhandler(400)
    def bad_request(e):
        return jsonify(error="Bad Request"), 400

    @app.errorhandler(403)
    def forbidden(e):
        # UI: render HTML page for forbidden access
        return render_template("errors/403.html"), 403

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify(error="Method Not Allowed"), 405

    return app


# Optional: module-level app for `flask run` / WSGI servers
app = create_app()
