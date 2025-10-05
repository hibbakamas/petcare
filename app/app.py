# app/app.py
# main entrypoint (factory pattern)

from flask import Flask, jsonify
from .config import Config
from .db import db, migrate
from .routes.api import api_blueprints
from .routes.ui import ui_blueprints

# --- time utilities for local rendering ---
from datetime import timezone
from zoneinfo import ZoneInfo


def create_app():
    """
    Application factory.
    Creates a fresh Flask app, wires config, DB, blueprints,
    Jinja filters, and JSON error handlers.
    """
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_object(Config)

    # init extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # register blueprints
    for bp in api_blueprints:
        app.register_blueprint(bp)
     # register blueprints
    for bp in ui_blueprints:
        app.register_blueprint(bp)

    # -------- Jinja filter: render datetimes in local timezone --------
    @app.template_filter("localdt")
    def localdt(dt, tz_name: str = "Europe/Madrid", fmt: str = "%Y-%m-%d %H:%M"):
        """
        Render a datetime in the given IANA timezone (default Europe/Madrid).
        - If dt is naive, treat it as UTC.
        - Returns '' for None.
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

    # -------- JSON error handlers --------
    @app.errorhandler(404)
    def not_found(e):
        return jsonify(error="Not Found"), 404

    @app.errorhandler(400)
    def bad_request(e):
        return jsonify(error="Bad Request"), 400

    @app.errorhandler(500)
    def internal_error(e):
        return jsonify(error="Internal Server Error"), 500

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify(error="Method Not Allowed"), 405

    return app


# Optional: module-level app for `flask run` / WSGI servers
app = create_app()