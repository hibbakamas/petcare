# main entrypoint

from flask import Flask, jsonify
from .config import Config
from .db import db, migrate
from .routes import blueprints

# --- time utilities for local rendering ---
from datetime import timezone
from zoneinfo import ZoneInfo

# create app and configure database
app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)
migrate.init_app(app, db)

# register blueprints
for bp in blueprints:
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

# return JSON instead of HTML for errors
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