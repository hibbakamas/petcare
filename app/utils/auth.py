"""API auth utilities: session-based login-required decorator."""

from functools import wraps
from typing import Any, Callable

from flask import jsonify, session


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
