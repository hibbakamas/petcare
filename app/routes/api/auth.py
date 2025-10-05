"""Auth API: signup, login, logout.

Session-based auth for the JSON API. Returns minimal JSON payloads and uses a
shared error helper for consistency across endpoints.
"""

from flask import Blueprint, request, session
from werkzeug.security import check_password_hash, generate_password_hash

from ...models import Users, db
from .helpers import json_error as _json_error  # shared JSON error helper

auth_bp = Blueprint("auth", __name__, url_prefix="/api/v1/auth")


@auth_bp.post("/signup")
def signup():
    """Create a new user and start a session.

    Request JSON:
        username: str (required)
        password: str (required)

    Returns:
        201 with {id, username} on success
        400 if fields are missing
        409 if username already exists
    """
    data = request.get_json(silent=True) or {}
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return _json_error("username and password required", 400)

    if Users.query.filter_by(username=username).first():
        return _json_error("username already taken", 409)

    user = Users(username=username, password_hash=generate_password_hash(password))
    db.session.add(user)
    db.session.commit()

    session["user_id"] = user.id
    return {"id": user.id, "username": user.username}, 201


@auth_bp.post("/login")
def login():
    """Authenticate a user and start a session.

    Request JSON:
        username: str (required)
        password: str (required)

    Returns:
        200 with {id, username} on success
        400 if fields are missing
        401 if credentials are invalid
    """
    data = request.get_json(silent=True) or {}
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return _json_error("username and password required", 400)

    user = Users.query.filter_by(username=username).first()
    if not user or not check_password_hash(user.password_hash, password):
        return _json_error("invalid credentials", 401)

    session["user_id"] = user.id
    return {"id": user.id, "username": user.username}, 200


@auth_bp.post("/logout")
def logout():
    """Clear the session."""
    session.clear()
    return "", 204
