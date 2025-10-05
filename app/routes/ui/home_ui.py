"""UI home route.

Redirects users to either the households index (if logged in) or the login page.
"""

from flask import Blueprint, redirect, session, url_for

home_ui = Blueprint("home_ui", __name__)


@home_ui.get("/")
def home():
    """Root path: choose destination based on session presence."""
    if session.get("user_id"):
        return redirect(url_for("households_ui.households_index"))
    return redirect(url_for("auth_ui.login_get"))
