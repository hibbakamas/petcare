# app/utils/auth.py
"""Auth utilities: session-based login-required decorators for API and UI."""

from functools import wraps
from typing import Any, Callable

from flask import jsonify, redirect, session, url_for


def login_required_api(fn: Callable[..., Any]) -> Callable[..., Any]:
    """Require an active session for JSON API routes.

    Returns 401 with {"error": "authentication required"} if no user_id is present.
    """

    @wraps(fn)
    def wrapper(*args: Any, **kwargs: Any):
        if not session.get("user_id"):
            return jsonify(error="authentication required"), 401
        return fn(*args, **kwargs)

    return wrapper


def login_required_ui(fn: Callable[..., Any]) -> Callable[..., Any]:
    """Require an active session for HTML UI routes.

    If no user_id is present, redirects to the login page.
    """

    @wraps(fn)
    def wrapper(*args: Any, **kwargs: Any):
        if not session.get("user_id"):
            return redirect(url_for("auth_ui.login_get"))
        return fn(*args, **kwargs)

    return wrapper